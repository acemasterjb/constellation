from os import environ, remove, scandir, pardir
from os.path import exists, dirname, abspath, join

from tkinter import filedialog, Tk
# from tkinter import Tk
from .DirectoryList import DirectoryList

musiclib = environ['USERPROFILE'] + '\\music'
root = Tk()


def b_to_i(in_bytes):
    """
        converts bytes to int then returns a time string:
        mm:ss
    """
    return("{:02}:{:02}".format(
        int(in_bytes / 6e4 % 60), int(in_bytes / 1e3 % 60)))


def dir_exists(file):
    return exists(file)


def is_audio(file):
    try:
        if file.endswith(('.mp3', '.flac',)):
            return True
    except Exception:
        pass
    return False


def i_del(item):
    remove(item)


def dir_name(directory):
    return dirname(directory)


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


def dirscanner(directory, llist):
    """
        Scan a directory and return a list of files and
        directories contained within.

        directory: iterator of os.DirEntry objects

        node: LinkedList node which every element in directory will be
              will be appended to. If the element is a folder, dirscanner
              will be called recursively to append its contents relative
              to the folder.
    """

    with scandir(directory) as folder:
        for element in folder:
            llist.append(element)
            if element.is_dir():
                folder_elem = llist[-1]
                nlist = DirectoryList()  # new linked list for folder contents
                folder_elem.down[0] = nlist.head
                folder_elem.up[0] = llist.head  # parent folder
                dirscanner(element, nlist)


def getpardir(currdir):
    """
        returns a <str> of the parent directory's path
    """
    return(abspath(join(currdir, pardir)))


def getdir(seek=0, wdir=musiclib):
    """
        Prompt to open a directory, scan it and return
        a list of files and directories contained within.

        If seek=1 then just scan a given directory (wdir)
        and return files and directories within.

        wdir: iterator of os.DirEntry objects
    """

    llist = DirectoryList()

    if seek and wdir:
        root.items = dirscanner(wdir, llist)
    else:
        wtitle = 'Choose music library'
        root.directory = filedialog.askdirectory(
            initialdir=wdir, title=wtitle)
        root.update()

        root.items = dirscanner(root.directory, llist)

        root.destroy()

    return(llist)
