import os
from libs.playsound.playsound import playsound
from tkinter import filedialog
from tkinter import *
import curses
from curses import wrapper
from keyboard import is_pressed

# - ask for directory
# - list songs in command window
# - choose song
# - give option for shuffle, repeat, etc
musiclib = os.environ['USERPROFILE'] + '\\music'
root = Tk()
# song = playsound()


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


def print_items(disp, menu, selected):
    """
        Prompt curses to print each entry in a given menu.

        disp: curses window
        menu: list of position: item pairs in a directory
        selected: position of cursor
    """

    disp.clear()
    disp.box()

    for i, item in enumerate(menu):
        if i == selected:
            disp.attron(curses.color_pair(1))
        disp.addstr(i, 0, item.name)
        disp.attroff(curses.color_pair(1))

    disp.refresh()


def nav_menu(disp, menu, selected):
    """
        Logic and actions for directory items.

        Handles selecting items and running them
        (if they are audio files)
        disp: curses window
        menu: list of position: item pairs in a directory
        selected: position of cursor

    """

    print_items(disp, menu, 0)
    p = playsound()

    while True:
        key = disp.getch()
        is_enter = (key == curses.KEY_ENTER or key in [10, 13])

        if key == curses.KEY_UP and selected > 0:
            selected -= 1
            print_items(disp, menu, selected)
        if key == curses.KEY_DOWN and selected < len(menu) - 1:
            selected += 1
            print_items(disp, menu, selected)

        if is_enter:
            if menu[selected].is_dir():
                top_dir = os.path.dirname(menu[0])
                prev = getdir(seek=1, wdir=os.path.dirname(top_dir))
                sel_path = menu[selected].path
                menu = getdir(1, sel_path)
                selected = 0
                print_items(disp, menu, selected)

            elif menu[selected].is_file():
                p.play(menu[selected].path, False)

        if key == ord('p'):
            if p.get_status() == 'playing':
                p.pause()
            elif p.get_status() == 'paused':
                p.resume(False)
            else:
                pass

        if is_pressed('ctrl+q'):
            if p.get_status() in ['playing', 'paused']:
                p.stop()
            break

        if key == ord('q'):
            menu = prev
            print_items(disp, menu, 0)


def main(stdscr):
    # stdscr.border(0)

    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    y, x = stdscr.getmaxyx()
    disp = curses.newwin(y - 3, x - 3, 3, 3)
    disp.keypad(True)
    # cmd = curses.newwin(5, x, 0, 0)

    curr_row = 0
    contents = getdir()

    nav_menu(disp, contents, curr_row)

    # disp.refresh()
    # disp.getkey()


# print()
wrapper(main)
