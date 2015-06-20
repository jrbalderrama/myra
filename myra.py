#!/usr/bin/env python

import errno
import os
import signal
import socket
import subprocess
import sys


STATIONS_FILE_NAME = ".myrarc"
# .mirarc file format located at $HOME dir
# ID URL <description>
# example:
#   cz1 http://netshow.play.cz:8000/radio1.mp3 Radio 1 CZ


def play(identifier, url, description=None, port=22222):
    """Play a radio.

    Play is a blocking action using sockets. It is not implemented with POSIX
    Local IPC Sockets (Unix domain sockets) because some OS implementations do
    not acknowledge the use of SO_REUSEADDR in case of AF_UNIX socket.
    """
    locksocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    locksocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        locksocket.bind(('localhost', port))
        locksocket.listen(0)
        message = '\tNow playing ' + \
                  (identifier if not description else description) + '!'
        command = ['mplayer', '-really-quiet', '-cache', '256', url]
        if url.endswith(('m3u', 'pls', 'asx')) or url.startswith('mms'):
            command.insert(-1, '-playlist')
        elif url.startswith('rtmp'):
            # rtmp streams require pipes between rtmpdump and mplayer
            # rtmpdump -v -r url | mplayer -
            # vlc -Idummy url
            print('the \'rtmp\' protocol is not supported!', file=sys.stderr)
            sys.exit(errno.ENOENT)
        print(message)
        execute(command)
    except OSError as error:
        if error.errno == 48:
            print('\tmyra radio player is already on!\n', file=sys.stderr)
        else:
            print(error, file= sys.stderr)
        sys.exit(errno.EALREADY)
    # else:
    #     #locksocket.shutdown(socket.SHUT_RDWR)
    #     locksocket.close()
    #     #sys.exit(os.EX_OK)


def execute(command):
    """Execute a system command as a sub-process.
    """
    try:
        with open(os.devnull, 'w') as null:
            process = subprocess.Popen(command,
                                       stdout=null,
                                       stderr=null,
                                       preexec_fn=os.setsid)
        process.communicate()
    except KeyboardInterrupt:
        # use process reset instead of the system call 'reset' to avoid the
        # terminal to hang after C-c. this avoid the terminal hangs after
        # killing the process with 'C-c' ref: stackoverflow #6488275
        process.send_signal(signal.SIGINT)
        # instead of 'process.terminate()' use os.killpg() to finish the
        # execution of all process' children. it works with the argument
        # preexec_fn=os.setsid) ref: stackoverflow #9117566
        os.killpg(process.pid, signal.SIGTERM)
    except OSError as error:
        print(error, file=sys.stderr)


def read_file(path):
    """Read a text file.
    """
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
            print('\tCannot play ' + parameter + '\n', sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
