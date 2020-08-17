from time import time
from threading import Timer
from tinytag import TinyTag


class Seek():
    """docstring for Seek"""

    def __init__(self, p):
        self.__running = True
        self.__paused = False
        self.p = p

    def print_seek(self, disp, menu, selected, len_b):
        song = menu[selected].path
        len_hms = "{:02}:{:02}:{:02}".format(
            len_b // 3600, len_b % 3600 // 60, len_b % 60)
        start = time()
        tag = TinyTag.get(song)
        y, x = disp.getmaxyx()

        disp.clear()
        meta = tag.artist + ' - ' + tag.title

        disp.addstr(int(y * 0.11), 0, '>')
        disp.addstr(int(y * 0.11), 2, meta)
        curr_time = (time() - start)
        disp.addstr(int(y * 0.11), int(x * 0.8),
                    "{:02}:{:02}:{:02}".format(curr_time // 3600, curr_time % 3600 // 60, curr_time % 60) + '/' + len_hms)

    def run_seek(self, seek, menu, selected, len_b):
        t = Timer(0.99, self.print_seek, args=(seek, menu, selected, len_b,))
        while self.__running:
            t.start()
            t.cancel()
        # self.print_seek(seek, menu, selected, len_b)
