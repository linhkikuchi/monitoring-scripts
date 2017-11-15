#!/usr/bin/python

import argparse
import telebot

def parse_args():
    parser = argparse.ArgumentParser(description='Nagios notification via Telegram')
    parser.add_argument('-c', '--contact', nargs='?', required=True)
    parser.add_argument('-t', '--type', nargs='?', required=True)
    parser.add_argument('-o', '--output', nargs='?', required=True)
    parser.add_argument('-m', '--monitor', nargs='?', required=True)
    parser.add_argument('-n', '--hostname', nargs='?', required=True)
    parser.add_argument('--hoststate', nargs='?')
    parser.add_argument('--hostaddress', nargs='?')
    parser.add_argument('--servicestate', nargs='?')
    parser.add_argument('--servicedesc', nargs='?')
    args = parser.parse_args()
    return args

def send_notification(token, user_id, message):
    bot = telebot.TeleBot(token)
    bot.send_message(user_id, message)

def host_notification(args):
    state = ''
    if args.hoststate == 'UP':
        state = u'\U00002705 '
    elif args.hoststate == 'DOWN':
        state = u'\U0001F525 '
    elif args.hoststate == 'UNREACHABLE':
        state = u'\U00002753 '

    return "%s%s - %s: %s [%s]" % (
        state,
        args.hostname,
        args.hostaddress,
        args.output,
        args.monitor,
    )

def service_notification(args):
    state = ''
    if args.servicestate == 'OK':
        state = u'\U00002705 '
    elif args.servicestate == 'WARNING':
        state = u'\U000026A0 '
    elif args.servicestate == 'CRITICAL':
        state = u'\U0001F525 '
    elif args.servicestate == 'UNKNOWN':
        state = u'\U00002753 '

    return "%s%s - %s: %s [%s]" % (
        state,
        args.hostname,
        args.servicedesc,
        args.output,
        args.monitor,
    )

def http_notification(args):
    state = u'\U00002757 '

    return "%s%s - %s [%s]" % (
        state,
        args.hostname,
        args.output,
        args.monitor,
    )

def main():
    args = parse_args()
    token = '308512174:AAH5XYYinFgu2i6O4ujVA8JAIHuQW8N04Dc'
    user_id = int(args.contact)
    if args.type == 'host':
        message = host_notification(args)
    elif args.type == 'service':
        message = service_notification(args)
    elif args.type == 'http':
        message = http_notification(args)
    send_notification(token, user_id, message)

if __name__ == '__main__':
    main()