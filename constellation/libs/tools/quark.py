from os import (
    environ, scandir, pardir, remove
)
from os.path import (
    abspath,
    dirname as _dirname,
    exists,
    join
)
from platform import system

from ..types.DirectoryList import DirectoryList

HOME = environ['USERPROFILE'] \
    if system() == "Windows" else \
    environ["HOME"]
MUSIC_DIR = join(HOME, "music")


def b_to_i(in_bytes):
    """
        converts bytes to int then returns a time string:
        mm:ss
    """
    return("{:02}:{:02}".format(
        int(in_bytes / 6e4 % 60), int(in_bytes / 1e3 % 60)))


def dir_exists(file: str):
    return exists(file)


def is_audio(file: str):
    try:
        if file.endswith(('.mp3', '.flac',)):
            return True
    except Exception:
        pass
    return False


def i_del(item: str):
    remove(item)


def dirname(directory: str):
    return _dirname(directory)


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


def dirscanner(directory: str, llist: DirectoryList):
    """
        Scan a directory and return a list of files and
        directories contained within.

        Parameters
        ---
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


def getdir(wdir=MUSIC_DIR) -> DirectoryList:
    """
        Gets file and child directory contents from a parent directory

        Parameters
        ---
        wdir: str - the working directory for this program

        Returns
        ---
        A `DirectoryList` containing a tree of directories and their files
    """

    llist = DirectoryList()
    dirscanner(
        wdir if dir_exists(wdir) else HOME,
        llist
    )

    return(llist)
