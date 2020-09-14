import curses
from curses import wrapper
import threading
from libs.tools import quark
from libs.tools import lumen

# - ask for directory
# - list songs in command window
# - choose song
# - give option for shuffle, repeat, etc
# song = playsound()


def main(stdscr):

    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    y, x = stdscr.getmaxyx()
    disp = curses.newwin(y, x, 0, 0)
    meta_panel = disp.subpad(int(y * 0.89), int(x * 0.19), 0, 0)
    files = disp.subpad(int(y * 0.89), int(x * 0.82), 0, int(x * 0.19))
    files.keypad(True)
    seek = disp.subpad(int(y * 0.11), x, int(y * 0.9), 0)
    # seek = disp.subpad(int(y * 0.14), x, int(y * 0.89), 0)
    # cmd = curses.newwin(5, x, 0, 0)

    contents = quark.getdir()

    player = lumen.Lumen(files, meta_panel, seek, contents)
    tui = threading.Thread(target=player.run_player())

    tui.start()

    # disp.refresh()
    # disp.getkey()


# print()
wrapper(main)
