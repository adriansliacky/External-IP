import httpx
import os
import datetime
import re
import csv
from colorama import Fore, Style
from os import path
from argparse import ArgumentParser

DEFAULT_DELAY = 300
IPV4_ENABLED = True
IPV6_ENABLED = True
SAVE_PATH = r'public_ip_history.csv'

parser = ArgumentParser(description='Tool for monitoring your external ip')

parser.add_argument('-c', action='store_false',
                    help='ignore connection errors')
parser.add_argument('-d', nargs='?', const=DEFAULT_DELAY, type=int,
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


def dtime_format_1():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-5]  # current time with decimal precision


def network_error(msg):
    if args.c:
        print(f'{dtime_format_1()} -{Fore.RED} network error {Style.RESET_ALL}- {msg}')
    else:
        exit(f'{Fore.RED}Please check your network connection and try again {Style.RESET_ALL}- {msg}')


def get_v4():
    v4_ = httpx.get('https://api.ipify.org').text
    # validate ipv4 address
    if re.search(r'(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}',
                 v4_):
        return v4_
    else:
        return '0.0.0.0'


def get_v6():
    v6_ = httpx.get('https://api64.ipify.org').text
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
            return ''
        elif first_mention == last_mention:
            return f' | last mention: {last_mention} ({l_diff.days} days)'
        else:
            f_diff = datetime.datetime.now() - datetime.datetime.strptime(first_mention, '%Y-%m-%d %H:%M:%S.%f')
            return f' | first mention: {first_mention} ({f_diff.days} days) | last mention: {last_mention} ({l_diff.days} days)'
    return ''


def main():
    test_n = 1

    try:
        print(f'Running test #{test_n} at {str(dtime_format_1())}')
        last_line = csv_get_last_line()

        if IPV4_ENABLED:
            ipv4 = get_v4()
            if not ipv4 == '0.0.0.0':
                print('IPv4 [' + u'{0}\u2713{1}'.format(Fore.GREEN, Style.RESET_ALL) + ']'
                      + f' - {ipv4}' + ip_mention(ipv4, 1))
            else:
                print('IPv4 [' + u'{0}\u2717{1}'.format(Fore.RED, Style.RESET_ALL) + ']')
        else:
            ipv4 = '-'
            print('IPv4 [' + u'{0}-{1}'.format(Fore.YELLOW, Style.RESET_ALL) + ']')

        if IPV6_ENABLED:
            ipv6 = get_v6()
            if not ipv6 == '::/0':
                print('IPv6 [' + u'{0}\u2713{1}'.format(Fore.GREEN, Style.RESET_ALL) + ']'
                      + f' - {ipv6}' + ip_mention(ipv6, 2))
            else:
                print('IPv6 [' + u'{0}\u2717{1}'.format(Fore.RED, Style.RESET_ALL) + ']')
        else:
            ipv6 = '-'
            print('IPv6 [' + u'{0}-{1}'.format(Fore.YELLOW, Style.RESET_ALL) + ']')
        test_n += 1

        print()

        is_new_ipv4 = last_line[1].strip() != ipv4
        if not is_new_ipv4:
            print('IPv4 did not change')
        else:
            print(f'your IPv4 changed, your new lease: {ipv4}')

        is_new_ipv6 = last_line[2].strip() != ipv6
        if not is_new_ipv6:
            print('IPv6 did not change')
        else:
            print(f'your IPv6 changed, your new lease: {ipv6}')

        if is_new_ipv4 or is_new_ipv6:
            csv_write_list([[str(dtime_format_1()), str(ipv4), str(ipv6)]])

        print('\n')
    except httpx.HTTPError as err:
        network_error(err)


if __name__ == '__main__':
    new_csv_file()
    main()
