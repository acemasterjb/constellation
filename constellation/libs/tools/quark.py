import os
from numpy import array
from tinytag import TinyTag
from tkinter import filedialog
from tkinter import *

musiclib = os.environ['USERPROFILE'] + '\\music'
root = Tk()


def b_to_i(in_bytes):
    """
        converts bytes to int then returns a time string:
        mm:ss
    """
    return("{:02}:{:02}".format(
        int(in_bytes / 6e4 % 60), int(in_bytes / 1e3 % 60)))


def dir_exists(file):
    return os.path.exists(file)


def is_audio(file):
    try:
        if file.endswith(('.mp3', '.flac',)):
            return True
    except Exception:
        pass
    return False


def i_del(item):
    os.remove(item)


def dirname(directory):
    return os.path.dirname(directory)


def check_album(song, key):
    """
        Checks if the song's album matches the given key
    """
    if song.album == key:
        return True


def check_artist(song, key):
    """
        Checks if the song's artist matches the given key
    """
    if song.artist == key:
        return True


def dirscanner(directory, check=None, criteria=None):
    """
        Scan a directory and return a list of files and
        directories contained within.

        directory: iterator of os.DirEntry objects

        check: function that checks if each item fits the criteria
               default=None; simply scan and return files in directory

        criteria: criteria to compare each item to if check param exists
    """

    with os.scandir(directory) as it:
        itemlist = []
        for item in it:
            if item.is_file() and check:
                if is_audio(item):
                    tag = TinyTag.get(item)
                    if check(tag, criteria):
                        itemlist.append(item)
                    continue
            itemlist.append(item)
        filelist = array(itemlist)
    return(filelist)


def getpardir(currdir):
    """
        returns a <str> of the parent directory's path
    """
    return(os.path.abspath(os.path.join(currdir, os.pardir)))


def getdir(seek=0, wdir=musiclib):
    """
        Prompt to open a directory, scan it and return
        a list of files and directories contained within.

        If seek=1 then just scan a given directory (wdir)
        and return files and directories within.

        wdir: iterator of os.DirEntry objects
    """

    if seek and wdir:
        root.items = dirscanner(wdir)
    else:
        wtitle = 'Choose music library'
        root.directory = filedialog.askdirectory(
            initialdir=wdir, title=wtitle)

        root.items = dirscanner(root.directory)

        root.destroy()

    return(root.items)
