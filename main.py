import db_writer, loader
import sys

boards = [ "int", "bant", "pol"]

print("Starting with arguments {}".format(str(sys.argv)))
if len(sys.argv) == 4:
    db_writer.set_login_details(sys.argv[1], sys.argv[2], sys.argv[3])
elif len(sys.argv) != 1:
    raise Exception("There should be 3(host, login, password) or 0 arguments, but {} given".format(str(sys.argv)))

while True:
    for board in boards:
        db_writer.write_archived_posts_from_board(board, check_for_repetition=True)

    for board in boards:
        db_writer.write_live_posts_from_board(board)

