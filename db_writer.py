from neo4j.v1 import GraphDatabase, basic_auth
import loader
import logger

_database = None
_verbose = True

_login = "neo4j"
_password = "pass"
_host = "localhost"


def set_login_details(host, login="neo4j", password="pass"):
    global _login, _password, _host
    _login = login
    _host = host
    _password = password


def get_session():
    global _database, _login, _host, _password
    if _database is None:
        _database = GraphDatabase.driver("bolt://{}:7687".format(_host), auth=basic_auth(_login, _password))
    return _database.session()


def write_posts_from_board(board):
    it = loader.read_all_posts_from_board_iterate_by_threads(board)
    write_iterable_posts(it, board)


def write_archived_posts_from_board(board, check_for_repetition=False):
    it = loader.read_archived_posts_from_board_iterate_by_threads(board)
    write_iterable_posts(it, board, check_for_repetition)


def write_live_posts_from_board(board):
    it = loader.read_live_posts_from_board_iterate_by_threads(board)
    write_iterable_posts(it, board)


def is_in_db(num):
    with get_session() as session:
        x = session.run("MATCH (a) WHERE (a:Post OR a:OpPost) AND a.n=$n RETURN a", n=int(num))
        for _ in x:
            return True
        return False


def write_iterable_posts(iterator, board, check_for_repetition=False):
    for thread_num, posts in iterator:
        if (not check_for_repetition) or (not is_in_db(thread_num)):
            for post_num in posts:
                write_post(post_num, posts[post_num])
            if _verbose:
                logger.write_log("Wrote thread {} from {}".format(thread_num, board))
        elif check_for_repetition:
            if _verbose:
                logger.write_log("Not writing repeated thread {} from {}".format(thread_num, board))


def write_post(number, post):
    with get_session() as session:
        if post['is_op']:
            session.run("MERGE (a:OpPost {n: $n}) "
                        "ON CREATE SET a += {text: $text, date: $date, board: $board} "
                        "MERGE (c:Country {code: $country}) "
                        "MERGE (a)-[:IS_FROM]->(c) ",
                        n=number, country=post['country'], text=post['text'], date=post['date'], board=post['board'])
        else:
            session.run("MERGE (a:Post {n: $n}) "
                        "ON CREATE SET a += {text: $text, date: $date} "
                        "MERGE (c:Country {code: $country}) "
                        "MERGE (a)-[:IS_FROM]->(c) "
                        "MERGE (op:OpPost {n: $n_op}) "
                        "MERGE (a)-[:OP_POST]->(op) ",
                        n=number, country=post['country'], text=post['text'], date=post['date'], n_op=post["thread"])

        for rt in post['replied_to']:
            session.run("MERGE (rt:Post {n: $n1}) "
                        "MERGE (a:Post {n: $n2}) "
                        "MERGE (a)-[:REPLIED_TO]->(rt) ",
                        n1=rt, n2=number)
