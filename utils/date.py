import time


def timestamp_to_time_string(time_stamp: int):
    time_array = time.localtime(time_stamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", time_array)
