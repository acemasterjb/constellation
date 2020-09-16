from curses import color_pair, KEY_ENTER, KEY_UP, KEY_DOWN
from libs.playsound.playsound import playsound
from keyboard import is_pressed
from time import sleep
from tinytag import TinyTag
import soundfile as sf
import numpy as np
from .quark import getdir, dir_exists, i_del


class Lumen():
    """
       Class for file browser and data panel widgets.
       Selects libraries and plays songs within them.

       print_side: Print to the panel widget
       nav_menu: Print and navigate directory entries.
       terminate: emergency thread terminate function
       print_items: print/draw items on curses widget/window
    """

    def __init__(self, disp, meta, seek, menu):
        self.p = playsound()
        self.is_playing = False
        self.__running = True

        self.disp = disp
        self.meta = meta
        self.seek = seek
        self.menu = menu
        self.prev = [self.menu]
        self.list = []
        self.selected = 0
        self.dtype = [('track', 'i4'), ('song', 'U500')]
        self.temp = "__play_temp.wav"
        self.q = 0

    def is_audio(self, file):
        """
            Currently supported file types:
           '.mp3', '.flac' and '.wav'
        """
        if file.endswith(('.mp3', '.flac', '.wav',)):
            return True
        return False

    def print_side(self, disp, q=None):
        """
            Print to the panel (left-most) widget.
        """

        disp.clear()

        p_len = disp.getmaxyx()[1] - 1  # printable length in window
        playlist = [TinyTag.get(song[1]).title for song in self.list]

        # album header
        disp.addnstr(1, 1, TinyTag.get(self.list[0][1]).album, p_len)
        disp.hline(2, 1, '-', p_len)  # h-line: -----------
        # songs in album
        for i in range(len(playlist)):
            if q and i == q:
                disp.attron(color_pair(1))
            disp.addnstr(i + 3, 1, playlist[i], p_len)
            disp.attroff(color_pair(1))
            disp.addstr('\n')

        disp.refresh()

    def print_items(self):
        """
            Prompt curses to print each entry in a given menu.

            self.disp: curses window
            self.menu: list of position: item pairs in a directory
        """

        self.disp.clear()
        self.disp.box()

        for i, item in enumerate(self.menu):
            if i == self.selected:
                self.disp.attron(color_pair(1))
            self.disp.addstr(i + 1, 1, item.name)
            self.disp.attroff(color_pair(1))

        self.disp.refresh()

    def prev(self):
        try:
            if self.q > 0:
                self.q -= 1
                # self.nav_entry(1, self.q, len(self.menu))
                self.play(self.list, self.meta, self.temp)
                self.print_items(self.disp, self.menu)
        except Exception:
            pass

    def next(self):
        try:
            if self.q < len(self.list) - 1:
                self.q += 1
                # self.nav_entry(1, self.q, len(self.menu))
                self.play(self.list, self.meta, self.temp)
                self.print_items(self.disp, self.menu)
        except Exception:
            print(Exception)

    def stop(self):
        try:
            if self.p.get_status() in ['playing', 'paused']:
                self.p.stop()
                self.p.close_alias()
                if dir_exists(self.temp):
                    i_del(self.temp)
                self.print_items(self.disp, self.menu)
        except Exception:
            print("No song in queue to stop")
            pass

    def play(self, menu, disp, temp=""):
        """
            Play the (self.q)th song from the given (menu).

            If a (temp) file
            is given and exists then it will delete it before it
            is used again for the next (self.q)th song.
        """

        if temp and dir_exists(temp):
            if self.is_playing:
                try:
                    self.p.stop()
                    self.p.close_alias()
                except Exception:
                    pass
            i_del(temp)

        song = menu[self.q][1]

        if song.endswith(('.flac')):
            with open(song, 'rb') as f:
                data, file_stream = sf.read(f)
                sf.write(temp, data, file_stream)
            del(data)
            del(file_stream)
            self.p.play(temp, False)

        else:
            self.p.play(song, False)

        self.is_playing = True
        self.print_side(disp, self.q)

    def quit(self):
        self.stop()
        self.terminate()

    def nav_menu(self, disp, seek, menu, key):
        """
            Logic and actions for directory items.

            Handles selecting items and running them
            (if they are audio files)
            disp: curses window
            menu: list of position: item pairs in a directory

        """
        file = self.menu[self.selected]
        is_enter = (key == KEY_ENTER or key in [10, 13])

        if key == KEY_UP and self.selected > 0:
            self.selected -= 1
            # self.nav_entry(0, self.selected, len(menu))
            self.print_items(disp, self.menu)
        if key == KEY_DOWN and self.selected < len(self.menu) - 1:
            self.selected += 1
            # self.nav_entry(1, self.selected, len(self.menu))
            self.print_items(disp, self.menu)

        if is_enter:
            if file.is_dir():
                self.prev.append(self.menu)
                sel_path = file.path
                self.menu = getdir(1, sel_path)
                self.selected = 0
                self.print_items(disp, self.menu)

            elif file.is_file():
                playlist = [
                    song.path for song in self.menu if self.is_audio(song.path)]
                idex = [(int(TinyTag.get(song).track) - 1)
                         for song in playlist]
                self.list = np.array(
                    list(zip(idex, playlist)), dtype=self.dtype)
                self.list = np.sort(self.list, order='track')

                try:
                    self.q = int(TinyTag.get(file.path).track) - 1
                except Exception:
                    print("No ID3 found for {}".format(file.path))
                    self.q = self.selected
                self.play(self.list, self.meta, self.temp)

        # if key == ord('s'):
        #     metadata = TinyTag.get(self.menu[self.selected].path)
        #     item = self.menu[self.selected].path

        #     playlist = dirscanner(
        #         dirname(item), check_album, metadata.album)

        #     self.p.play(playlist, False)

        if key == ord('p'):
            if self.p.get_status() == 'playing':
                self.p.pause()
            elif self.p.get_status() == 'paused':
                self.p.resume(False)

        if key == ord('q'):
            self.menu = self.prev.pop()
            self.selected = 0
            self.print_items(disp, self.menu)
        self.print_items(self.disp, self.menu)
        sleep(0.025)

    def terminate(self):
        """
            Terminate thread / shut down application
        """
        self.__running = False

    def run_player(self):
        """
            For thread compatibility, along with self.terminate()
        """
        self.print_items(self.disp, self.menu)
        while self.__running:
            key = self.disp.getch()
            if is_pressed('ctrl + comma'):
                self.prev()
                continue

            if is_pressed('ctrl + period'):
                self.next()
                continue

            if is_pressed('ctrl + q'):
                self.quit()
                continue

            if is_pressed('ctrl + s'):
                self.stop()
                continue

            self.nav_menu(self.disp, self.seek,
                          self.menu, key)

        if dir_exists(self.temp):
            i_del(self.temp)
