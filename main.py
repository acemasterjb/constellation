import os
from playsound import playsound
from tkinter import filedialog
from tkinter import *
from pathlib import Path
import curses
from curses import wrapper

# - ask for directory
# - list songs in command window
# - choose song
# - give option for shuffle, repeat, etc

# initialize cmd to run curse
stdscr = curses.initscr()

# # turn off key echoing in cmd
# curses.noecho()
# # execute commands without 'Enter'
# curses.cbreak()
# # allow curses to handle special nav keys
# stdscr.keypad(True)

# # the following 3 statements terminates curses
# curses.nocbreak()
# stdscr.keypad(False)
# curses.echo()

# # restore cmd to default
# curses.endwin()

# window dimensions
begin_x = 20
begin_y = 7
height = 5
width = 40

musiclib = os.environ['USERPROFILE'] + '\\music'
root = Tk()

# initialize window
win = curses.newwin(height, width, begin_y, begin_x)

def dirscanner(dirlist):

    filelist = []
    with os.scandir(dirlist) as it:
        for file in it:
            if file.is_dir():
                filelist.append(dirscanner(file.path))
            if not file.name.startswith('.') and file.is_file():
                filelist.append(file.path)

    return(filelist)

def getdir(parent=musiclib):

    wtitle = 'Choose music library'
    root.directory = filedialog.askdirectory(
        initialdir=musiclib, title=wtitle)
    root.files = []



    return(root.files)


def list_menu(stdscr, menu):
    stdscr.clear()

    for i, item in enumerate(menu):
        stdscr.addstr(i, 0, item)


def main(stdscr):

    files = getdir()

    list_menu(stdscr, files)

    # Clear screen
    # stdscr.clear()

    # defines color pairs; this one is red fore, white back
    # curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
    # stdscr.addstr(0, 0, "Pretty text", curses.color_pair(1))

    # # This raises ZeroDivisionError when i == 10.
    # for i in range(0, 11):
    #     v = i - 10
    #     stdscr.addstr(i, 0, '10 divided by {} is {}'.format(v, 10 / v))

    stdscr.refresh()
    stdscr.getkey()


wrapper(main)
