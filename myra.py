#!/usr/bin/env python

import errno
import os
import tempfile
import subprocess
import sys
from lockfile import FileLock

STATIONS_FILE_NAME = ".myrarc"
# .mirarc file format located at $HOME dir
# ID URL <description>
# example:
# cz1 http://netshow.play.cz:8000/radio1.mp3 Radio 1 CZ


class Radio(object):


    def __init__(self, identifier, url, description=None):
        self.identifier = identifier
        self.url = url
        self.description = description

    def play(self):
        lockfile = FileLock(tempfile.gettempdir() + os.sep + STATIONS_FILE_NAME)
        if lockfile.is_locked():
            sys.stderr.write('\tmyra radio player is already on!\n')
            sys.exit(errno.EALREADY)
        with lockfile:
            message = '\tNow playing ' + \
                      (self.identifier if not self.description else self.description) + '!'
            command = ['mplayer', '-really-quiet', '-cache', '256', self.url]
            if self.url.endswith(('m3u', 'pls', 'asx')) or \
               self.url.startswith('mms'):
                command.insert(-1, '-playlist')
            elif self.url.startswith('rtmp'):
                print('work in progress')
                # TODO support rtmp streams using pipes
                # between rtmpdump and mplayer
                # vlc -Idummy URL
                # cmd=['rtmpdump', '-v', '-r', self.url, '|', 'mplayer', '-']
            print(message)
            execute(command, True)


def execute(command, devnull=False):
    try:
        if not devnull:
            subprocess.call(command)
        else:
            with open(os.devnull, 'w') as filenull:
                subprocess.call(command, stdout=filenull, stderr=filenull)
    except KeyboardInterrupt:
        # todo add pythonic reset
        command = ['reset']
        subprocess.call(command)
        sys.exit(errno.EINTR)
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
        for item in radios:
            print('\t' + item[0] + '\t' + ''.join(item[2:]).rstrip())
        sys.exit(errno.EAGAIN)
    parameter = argv[0]
    try:
        identifier = None
        url = None
        description = None
        if '://' not in parameter:
            dictionary = dict([(column[0], (column[1], ''.join(column[2:]).rstrip()))
                               for column in radios])
            identifier = parameter
            url = dictionary[parameter][0]
            description = dictionary[parameter][1]
        else:
            identifier = "radio from URL"
            url = parameter
        radio = Radio(identifier, url, description)
        radio.play()
    except KeyError:
        sys.stderr.write('\tCannot play ' + parameter + '\n')


if __name__ == "__main__":
    main(sys.argv[1:])
