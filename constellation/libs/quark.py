import os
from tkinter import filedialog
from tkinter import *

musiclib = os.environ['USERPROFILE'] + '\\music'
root = Tk()


def dir_exists(file):
    return os.path.exists(file)


def i_del(item):
    os.remove(item)


def dirname(directory):
    return os.path.dirname(directory)


def dirscanner(directory):
    """
        Scan a directory and return a list of files and
        directories contained within.

        directory: iterator of os.DirEntry objects
    """

    filelist = []
    with os.scandir(directory) as it:
        for item in it:
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
