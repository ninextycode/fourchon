import datetime

def write_log(text, log_dir="log.txt"):
    with open(log_dir, "a+") as f:
        f.write("{}: {}\n".format(datetime.datetime.now().strftime("%d.%m.%y %H:%M:%S"), text))