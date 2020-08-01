import os
# from libs.playsound.playsound import playsound
from tkinter import filedialog
from tkinter import *
# from pathlib import Path
import curses
from curses import wrapper
# import socket
from threading import Thread
# from keyboard import is_pressed
# from queue import Queue
from lumen import player
# import daemon

# - ask for directory
# - list songs in command window
# - choose song
# - give option for shuffle, repeat, etc

musiclib = os.environ['USERPROFILE'] + '\\music'
root = Tk()
# song = playsound()

def dirscanner(dirlist):

    filelist = []
    with os.scandir(dirlist) as it:
        for item in it:
            filelist.append(item)

    return(filelist)

def getdir(seek=0, wdir=musiclib):

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

    disp.clear()
    disp.box()

    for i, item in enumerate(menu):
        if i == selected:
            disp.attron(curses.color_pair(1))
        disp.addstr(i, 0, item.name)
        disp.attroff(curses.color_pair(1))

    disp.refresh()


def nav_menu(disp, menu, selected):

    # p = playsound()

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
                # q = Queue
                p = player()
                t = Thread(target=p.run, args=(menu[selected].path,))
                t.start()
                t.join()
        # try:
        #     if key == ord('p'):
        #         t = Thread(target=p.get_status)
        #         if t.start() == "playing":
        #             t = Thread(target=p.pause)
        #             t.start()
        #             continue
        #         t = Thread(target=p.resume, args=(False,))
        #         t.start()
        #         t.join()
        # except Exception as e:
        #     raise e
        # else:
        #     pass
        # finally:
        #     pass
        if key == ord('q'):
            menu = prev
            print_items(disp, menu, 0)
        # if is_pressed('ctrl+q'):
        #     t = Thread(target=p.stop())
        #     t.start()
        #     t.join()


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

    disp.refresh()
    disp.getkey()


# print()
wrapper(main)
