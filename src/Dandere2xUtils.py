import os
import time


# waits for a text file, then returns
def wait_on_text(text_file):
    exists = exists = os.path.isfile(text_file)
    count = 0
    while not exists:
        if count % 1000 == 0:
            print(text_file, "dne")
        exists = os.path.isfile(text_file)
        count += 1
        time.sleep(.2)

    file = open(text_file, "r")

    text_list = file.read().split('\n')
    file.close()

    if len(text_list) == 1:
        return []

    return text_list


def wait_on_file(file_string):
    exists = exists = os.path.isfile(file_string)
    count = 0
    while not exists:
        if count % 1000 == 0:
            print(file_string, "dne")
        exists = os.path.isfile(file_string)
        count += 1
        time.sleep(.001)


def get_lexicon_value(digits, val):
    string = str(val)

    while (len(string) < digits):
        string = '0' + string

    return string


def main():
    text = wait_on_text("/home/linux/Videos/newdebug/yn2/pframe_data/pframe_1.txt")


if __name__ == "__main__":
    main()
