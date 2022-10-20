import requests
from colorama import Fore
from colorama import Style
import time
import sched
import os
from os import path
import datetime
import re
import csv
import argparse

# Instantiate the parser
default_delay = 300
parser = argparse.ArgumentParser(
    description='App for monitoring your external ip')

parser.add_argument('-c', action='store_true',
                    help='ignore connection errors')
parser.add_argument('-d', nargs='?', const=default_delay, type=int,
                    help='delay between each run in seconds, default is 300')
args = parser.parse_args()

if args.d is None:
    args.d = default_delay

if args.d < 1:
    parser.error('delay_arg cannot be smaller than 1')

print(args.d)


def dtime_format_1():
    return ((datetime.datetime.now()).strftime(
        '%Y-%m-%d %H:%M:%S.%f'))[:-5]  # returns current time with decimal precision


def network_error(msg):
    if args.c:
        print(
            f'{dtime_format_1()} -{Fore.RED} network error {Style.RESET_ALL}- {msg}')
    else:
        print(
            f'{Fore.RED}Please check your network connection and try again {Style.RESET_ALL}- {msg}')
        exit()


def get_v4():
    v4_ = requests.get('https://api.ipify.org').text

    # validate ipv4 address
    if re.search(r'(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}', v4_
                 ) is not None:
        return v4_
    else:
        return '0.0.0.0'


def get_v6():
    v6_ = requests.get('https://api64.ipify.org').text

    # validate ipv6 address
    if re.search(r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,'
                 r'6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,'
                 r'4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,'
                 r'2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,'
                 r'7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2['
                 r'0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,'
                 r'4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,'
                 r'1}[0-9]))', v6_):
        return v6_
    else:
        return '::/0'


"""
csv
"""
###

path_to_file = r'public_ip_history.csv'

"""
header
"""
file_header = ['time', 'ipv4', 'ipv6']

try:
    f_size = os.path.getsize(path_to_file)
except FileNotFoundError as e:
    pass

make_csv_header = False
if not path.exists(path_to_file) or f_size == 0:
    make_csv_header = True

with open(path_to_file, 'a', newline='') as file:
    writer = csv.writer(file)
    if make_csv_header:
        writer.writerow(file_header)

"""
header
"""


def csv_write_list(data_to_write):
    with open(path_to_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data_to_write)


def csv_get_last_line(filepath=path_to_file):
    with open(filepath) as file:
        for line in file:
            pass
    return line.split(',')


###
"""
csv
"""
x = 1


def main():
    try:
        global x
        print(f'Running test #{x} at {str(dtime_format_1())}')
        ipv4 = get_v4()
        if not ipv4 == '0.0.0.0':
            print(
                'ipv4 [' + u'{0}\u2713{1}'.format(Fore.GREEN, Style.RESET_ALL) + ']' + f' - {ipv4}')
        else:
            print(
                'ipv4 [' + u'{0}\u2717{1}'.format(Fore.RED, Style.RESET_ALL) + ']')

        ipv6 = get_v6()
        if not ipv6 == '::/0':
            print(
                'ipv6 [' + u'{0}\u2713{1}'.format(Fore.GREEN, Style.RESET_ALL) + ']' + f' - {ipv6}')
        else:
            print(
                'ipv6 [' + u'{0}\u2717{1}'.format(Fore.RED, Style.RESET_ALL) + ']')
        x += 1

        last_line = csv_get_last_line()

        print()
        is_new_ipv4 = (last_line[1].strip() != ipv4)
        if not is_new_ipv4:
            print('ipv4 didn\'t change')
        else:
            print(f'your ipv4 changed, your new lease: {ipv4}')
        is_new_ipv6 = (last_line[2].strip() != ipv6)
        if not is_new_ipv6:
            print('ipv6 didn\'t change')
        else:
            print(f'your ipv6 changed, your new lease: {ipv6}')

        if is_new_ipv4 or is_new_ipv6:
            csv_write_list(
                [[str(dtime_format_1()), str(ipv4), str(ipv6)]])
        print('\n')
    except requests.exceptions.ConnectionError as e:
        network_error(e)


delay = args.d

s = sched.scheduler(time.time, time.sleep)


def schedule(sc):
    main()
    ###
    sc.enter(delay, 1, schedule, (sc,))


main()  # execute main for first time
s.enter(delay, 1, schedule, (s,))
s.run()
