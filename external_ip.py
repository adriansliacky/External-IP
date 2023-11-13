import httpx
import os
import datetime
import re
import csv
import time
import sched
from colorama import Fore, Style
from os import path
from argparse import ArgumentParser

DEFAULT_DELAY = 300
IPV4_ENABLED = True
IPV6_ENABLED = True
SAVE_PATH = r'public_ip_history.csv'

parser = ArgumentParser(description='Tool for monitoring your external ip')

parser.add_argument('-c', action='store_false',
                    help='halt on connection errors')
parser.add_argument('-d', nargs='?', const=DEFAULT_DELAY, type=float,
                    help=f'delay between each run in seconds, default is {DEFAULT_DELAY}')
parser.add_argument('-f', nargs='?', const=SAVE_PATH, type=str,
                    help=f'log save location, default is {SAVE_PATH}')
args = parser.parse_args()

if args.d is None:
    args.d = DEFAULT_DELAY
if args.f is None:
    args.f = SAVE_PATH

if args.d < 1:
    parser.error('delay argument cannot be smaller than 1')

delay = args.d
path_to_file = args.f

NULL_V4, NULL_V6, NA = '0.0.0.0', '::/0', '-'


def dtime_format_1():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-5]  # current time with decimal precision


def network_error(msg):
    if args.c:
        print(f'{dtime_format_1()} -{Fore.RED} network error {Style.RESET_ALL}- {msg}\n\n')
    else:
        exit(f'{Fore.RED}Please check your network connection and try again {Style.RESET_ALL}- {msg}')


def get_v4():
    addr = httpx.get('https://api.ipify.org').text
    # validate ipv4 address
    if re.search(r'(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}',
                 addr):
        return addr
    else:
        return NULL_V4


def get_v6():
    addr = httpx.get('https://api64.ipify.org').text
    # validate ipv6 address
    if re.search(r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,'
                 r'6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,'
                 r'4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,'
                 r'2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,'
                 r'7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2['
                 r'0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,'
                 r'4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,'
                 r'1}[0-9]))', addr):
        return addr
    else:
        return NULL_V6


def new_csv_file():
    file_header = ['time', 'ipv4', 'ipv6']

    try:
        f_size = os.path.getsize(path_to_file)
    except FileNotFoundError:
        f_size = 0

    if not path.exists(path_to_file) or f_size == 0:
        with open(path_to_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(file_header)


def csv_write_list(data_to_write):
    with open(path_to_file, 'a', newline='') as f:
        csv.writer(f).writerows(data_to_write)


def csv_get_last_line(filepath=path_to_file):
    with open(filepath) as f:
        return f.readlines()[-1].split(',')


def ip_mention(addr, v):
    first_mention = ''
    mention_text = ' (new lease)'
    for line in open(path_to_file).readlines():
        if line.split(',')[v].strip() == addr:
            first_mention = line.split(',')[0]
            break
    if first_mention:
        last_mention = ''
        for line in open(path_to_file).readlines()[::-1]:
            if line.split(',')[v].strip() == addr:
                last_mention = line.split(',')[0]
                break
        l_diff = datetime.datetime.now() - datetime.datetime.strptime(last_mention, '%Y-%m-%d %H:%M:%S.%f')
        if not last_mention:
            return mention_text
        elif first_mention == last_mention:
            return f' | last mention: {last_mention} ({l_diff.days} days)'
        else:
            f_diff = datetime.datetime.now() - datetime.datetime.strptime(first_mention, '%Y-%m-%d %H:%M:%S.%f')
            return f' | first mention: {first_mention} ({f_diff.days} days) | last mention: {last_mention} ({l_diff.days} days)'
    return mention_text


def test(l_addr, v):
    if v == 1:
        v_txt = 'IPv4'
        addr = get_v4()
    else:
        v_txt = 'IPv6'
        addr = get_v6()
    return_is_new = False
    if not addr == (NULL_V4 if v == 1 else NULL_V6):
        is_new = l_addr.strip() != addr
        return_is_new = is_new
        if not is_new:
            print('(unchanged)', end=' ')
        else:
            print('{0}(changed){1}'.format(Fore.YELLOW, Style.RESET_ALL), end=' ')
        print(v_txt + ' [' + u'{0}\u2713{1}'.format(Fore.GREEN, Style.RESET_ALL) + ']'
              + f' - {addr}' + ip_mention(addr, v))
    else:
        print(v_txt + ' [' + u'{0}\u2717{1}'.format(Fore.RED, Style.RESET_ALL) + ']')
    return addr, return_is_new


def skip_v(v):
    if v == 1:
        v_txt = 'IPv4'
    else:
        v_txt = 'IPv6'
    print(v_txt + ' [' + u'{0}-{1}'.format(Fore.YELLOW, Style.RESET_ALL) + ']')


test_n = 1


def main():
    global test_n

    try:
        print(f'Running test #{test_n} at {str(dtime_format_1())}')
        test_n += 1
        last_v4, last_v6 = csv_get_last_line()[1:]
        is_new_ipv4, is_new_ipv6 = False, False

        if IPV4_ENABLED:
            ipv4, is_new_ipv4 = test(last_v4, 1)
        else:
            ipv4 = NA
            skip_v(1)

        if IPV6_ENABLED:
            ipv6, is_new_ipv6 = test(last_v6, 2)
        else:
            ipv6 = NA
            skip_v(2)

        if is_new_ipv4 or is_new_ipv6:
            csv_write_list([[str(dtime_format_1()), str(ipv4), str(ipv6)]])

        print('\n')
    except httpx.HTTPError as err:
        network_error(err)


def schedule(sc):
    sc.enter(delay, 1, schedule, (sc,))
    main()


if __name__ == '__main__':
    new_csv_file()
    main()
    s = sched.scheduler(time.time, time.sleep)
    s.enter(delay, 1, schedule, (s,))
    s.run()
