import curses
from curses import (
    wrapper, color_pair, KEY_ENTER, KEY_UP, KEY_DOWN
)
from keyboard import is_pressed

def directory_lister(stdscr):
    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    y, x = stdscr.getmaxyx()
    disp = curses.newwin(y, x, 0, 0)
    meta_panel = disp.subpad(int(y * 0.89), int(x * 0.19), 0, 0)
    files = disp.subpad(int(y * 0.89), int(x * 0.82), 0, int(x * 0.19))
    files.nodelay(True)
    files.keypad(True)