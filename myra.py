#!/usr/bin/env python

from lockfile import FileLock
import errno
import os
import readline
import tempfile
import subprocess
import sys

STATIONS_FILE_NAME = ".myrarc"
# .mirarc file format located at $HOME dir
# ID URL <description>
# example: 
# cz1 http://netshow.play.cz:8000/radio1.mp3 Radio 1 CZ

class Radio:

    def __init__(self, identifier, url, description = None):
        self.identifier = identifier
        self.url = url
        self.description = description

    def play(self):
        lockfile = FileLock(tempfile.gettempdir() + os.sep + STATIONS_FILE_NAME)        
        if lockfile.is_locked():
            sys.stderr.write('\tradio player is already on!\n')
            sys.exit(errno.EALREADY)
        with lockfile:
            message = 'now playing ' + (self.identifier if not self.description
                                        else self.description) + '!'
            command = ['cowsay', '-W' ,'13', message]
            execute(command)
            command = ['mplayer', '-really-quiet', '-cache', '256', self.url]
            if self.url.endswith(('m3u','pls')) or self.url.startswith('mms'): 
                command.insert(-1,'-playlist')
            execute(command, True)

def execute(command, devnull = False):
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
        for item in radios: print('\t' + item[0] + '\t' + ''.join(item[2:]).rstrip())
        sys.exit(errno.EAGAIN)
    try:
        dictionary = dict([(column[0], (column[1],''.join(column[2:]).rstrip())) for column in radios])
        radio = Radio(argv[0], dictionary[argv[0]][0], dictionary[argv[0]][1])
        print 
        radio.play()
    except KeyError:
        sys.stderr.write('\tRadio station ' + argv[0] + ' is not registered!\n')

if __name__ == "__main__":
    main(sys.argv[1:])
