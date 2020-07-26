import os
from libs.playsound.playsound import playsound
from tkinter import filedialog
from tkinter import *
# from pathlib import Path
import curses
from curses import wrapper
# import socket
import threading
# import daemon

# - ask for directory
# - list songs in command window
# - choose song
# - give option for shuffle, repeat, etc

musiclib = os.environ['USERPROFILE'] + '\\music'
root = Tk()
song = playsound()

def dirscanner(dirlist):

    filelist = []
    with os.scandir(dirlist) as it:
        for item in it:
            filelist.append(item)

    return(filelist)

def getdir(seek=0, wdir=musiclib):

    if seek:
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


def list_menu(disp, menu, selected):

    while True:
        print_items(disp, menu, selected)

        key = disp.getch()
        is_enter = (key == curses.KEY_ENTER or key in [10, 13])

        disp.clear()

        if key == curses.KEY_UP and selected > 0:
            selected -= 1
        if key == curses.KEY_DOWN and selected < len(menu) - 1:
            selected += 1
        if key == ord('p'):
            if song.get_status() == 'paused':
                song.resume()
            else:
                try:
                    song.pause()
                except:
                    break

        if key == ord('q'):
            """
                - position cursor to len(win) - 1, 0
                - show cursor
                - accept input
                - if 'q', quit
            """
            try:
                thread.stop()
                break
            except:
                break
        elif is_enter:
            if menu[selected].is_dir():
                contents = getdir(seek=1, wdir=menu[selected].path)
                list_menu(disp, contents, 0)
            elif menu[selected].is_file():
                # if song.get_status == "playing":
                #     thread.stop()
                # create and start a thread that plays music
                thread = threading.Thread(target=song.play,
                                          args=[menu[selected].path])
                thread.start()


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

    list_menu(disp, contents, curr_row)

    disp.refresh()
    disp.getkey()


# print()
wrapper(main)
