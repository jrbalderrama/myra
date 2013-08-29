#!/usr/bin/env python3

import errno
import os
import signal
import socket
import subprocess
import sys


STATIONS_FILE_NAME = ".myrarc"
## .mirarc file format located at $HOME dir
## ID URL <description>
## example:
##   cz1 http://netshow.play.cz:8000/radio1.mp3 Radio 1 CZ


def play(identifier, url, description=None):
    locksocket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        ## lock program using domain sockets
        locksocket.bind('\0' + os.path.basename(__file__))
        message = '\tNow playing ' + \
                  (identifier if not description else description) + '!'
        command = ['mplayer', '-really-quiet', '-cache', '256', url]
        if url.endswith(('m3u', 'pls', 'asx')) or url.startswith('mms'):
            command.insert(-1, '-playlist')
        elif url.startswith('rtmp'):
            # rtmp streams require pipes between rtmpdump and mplayer
            # rtmpdump -v -r url | mplayer -
            # vlc -Idummy url
            print('the \'rtmp\' protocol is not supported!')
            sys.exit(errno.ENOENT)
        print(message)
        execute(command)
    except socket.error:
        sys.stderr.write('\tmyra radio player is already on!\n')
        sys.exit(errno.EALREADY)


def execute(command):
    try:
        with open(os.devnull, 'w') as null:
            process = subprocess.Popen(command, stdout=null, stderr=null,
                                       preexec_fn=os.setsid)
        process.communicate()
    except KeyboardInterrupt:
        # pythonic reset instead of os.system('reset')
        # this avoid the terminal hangs after C-c
        # ref: stackoverflow #6488275
        process.send_signal(signal.SIGINT)
        ## instead of process.terminate() killpg will finish execution
        ## of all process' children (works with preexec_fn=os.setsid)
        # ref: stackoverflow #9117566
        os.killpg(process.pid, signal.SIGTERM)
    except OSError:
        sys.stderr.write('\tcommand \'' + command[0] + '\' not found!\n')
        sys.exit(errno.ENOENT)


def read_file(path):
    with open(path) as _file:
        _list = _file.readlines()
    return _list


def main(argv):
    path = os.path.join(os.getenv('HOME'), STATIONS_FILE_NAME)
    lines = read_file(path)
    # radios = map(lambda x: x.split(None, 2), descriptions)
    radios = [line.split(None, 2) for line in lines]
    if not argv:
        print('Usage: myra [ID|URL]\n')
        print('\tID\tdescription\n')
        print(radios)
        for item in radios:
            print('\t' + item[0] + '\t' + ''.join(item[2:]).rstrip())
        sys.exit(errno.EAGAIN)
    else:
        parameter = argv[0]
        try:
            if '://' not in parameter:
                dictionary = dict([
                    (column[0], (column[1], ''.join(column[2:]).rstrip()))
                    for column in radios])
                identifier = parameter
                url = dictionary[parameter][0]
                description = dictionary[parameter][1]
            else:
                identifier = "radio from URL"
                url = parameter
            play(identifier, url, description)
        except KeyError:
            sys.stderr.write('\tCannot play ' + parameter + '\n')


if __name__ == "__main__":
    main(sys.argv[1:])
