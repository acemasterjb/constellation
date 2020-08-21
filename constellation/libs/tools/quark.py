import os
from tinytag import TinyTag
from tkinter import filedialog
from tkinter import *

musiclib = os.environ['USERPROFILE'] + '\\music'
root = Tk()


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


def check_album(tag, criteria):
    if tag.album == criteria:
        return True


def check_artist(item, criteria):
    if item.artist == criteria:
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

    filelist = []
    with os.scandir(directory) as it:
        for item in it:
            if item.is_file():
                if is_audio(item):
                    tag = TinyTag.get(item)
                    if check and check(tag, criteria):
                        filelist.append(item)
                    continue
            filelist.append(item)
    return(filelist)


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
