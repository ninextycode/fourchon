import requests
import json
import time
import re

_timer_start_time = None
_use_timer = False


def restart_timer():
    global _timer_start_time
    _timer_start_time = time.time()


def timer():
    global _timer_start_time
    if _timer_start_time is None:
        raise Exception("Timer not started")
    return time.time() - _timer_start_time

restart_timer()


def catalog_request_url(board, archive=False):
    return r'http://a.4cdn.org/{}/{}.json'\
        .format(board, 'archive' if archive else 'threads')


def thread_request_url(board, thread_num):
    return r'http://a.4cdn.org/{}/thread/{}.json'.format(board, thread_num)


def get_json_thread(board, thread_num):
    request = thread_request_url(board, thread_num)
    json_data =  get_json_exept(request)
    json_data["board"] = board
    return json_data

def get_json_exept(request, wait=_use_timer):
    if wait:
        while timer() < 1.1:
            time.sleep(0.05)

    try:
        response = requests.get(request)
    except Exception as e:
        raise Exception("Exception trying to get {}:\n".format(request) + str(e))
    finally:
        restart_timer()
    if response.status_code != 200:
        raise Exception("Status code of {} request is {}".format(request, response.status_code))
    return response.json()


def get_thread_numbers(board, archive=False):
    request = catalog_request_url(board, archive)
    if archive:
        threads = get_archived_threads(request)
    else:
        threads = get_live_treads(request)
    threads = list(threads)
    threads.sort()
    return threads


def get_archived_threads(request):
    return get_json_exept(request)


def get_live_treads(request):
    live_response = get_json_exept(request)
    return list_of_threads_from_live_thread_numbers_response(live_response)


def list_to_file(filename, l):
    with open(filename, 'w') as f:
        f.write("[\n")
        for i in l[:-1]:
            f.write("\t{},\n".format(str(i)))

        if len(l) > 0:
            f.write("\t{}\n".format(str(l[-1])))
        f.write("]\n")


def json_to_file(filename, json_obj):
    with open(filename, "w") as f:
        json.dump(obj=json_obj, fp=f, indent=4)


# archive request returns a list of threads,
# but live request returns some additional data which should be filtered
def list_of_threads_from_live_thread_numbers_response(live_response):
    threads = []
    for page in live_response:
        for thread in page['threads']:
            threads.append(thread['no'])
    return threads


def whom_replied(post):
    it = re.finditer(r"<a href=\"#p(\d+)\" class=\"quotelink\">", post)
    replied = [m.group(1) for m in it]
    replied.sort()
    return replied


def posts_in_thread(board, thread_number):
    return posts_in_json_thread(get_json_thread(board, thread_number))


def posts_in_json_thread(json_thread):
    connections = {}
    for post in json_thread['posts']:
        replied = [int(r) for r in whom_replied(post.get("com", "")) if int(r) != int(post["resto"])]

        if "country" in post.keys():
            country = post["country"]
        elif "troll_country" in post.keys():
            country = "troll_" + post["troll_country"]
        else:
            country = "n/a"

        connections[post['no']] = {
            "country": country,
            "replied_to": replied ,
            "thread": int(post["resto"]),
            "is_op": int(post["resto"]) == 0,
            "text": post.get("com", ""),
            "date": post["now"],
            "board": json_thread["board"]
        }
    return connections


def read_archived_posts_from_board_iterate_by_threads(board):
    thread_nums = get_thread_numbers(board, archive=True)
    for t in thread_nums:
        yield (t, posts_in_thread(board, t))


def read_live_posts_from_board_iterate_by_threads(board):
    threads = get_thread_numbers(board, archive=False)
    for t in threads:
        yield (t, posts_in_thread(board, t))


def read_all_posts_from_board_iterate_by_threads(board):
    threads = get_thread_numbers(board, archive=True)
    live_threads = get_thread_numbers(board, archive=False)
    threads.extend([l for l in live_threads if l not in threads])
    for t in threads:
        yield (t, posts_in_thread(board, t))