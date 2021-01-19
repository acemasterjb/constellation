from curses import color_pair, KEY_ENTER, KEY_UP, KEY_DOWN
from libs.playsound.playsound import playsound
from keyboard import is_pressed
from time import sleep
from tinytag import TinyTag
import soundfile as sf
import numpy as np
from .quark import getdir, dir_exists, i_del, getpardir, b_to_i


class Lumen():
    def __init__(self, disp, meta, seek, menu):
        """
           Class for file browser and data panel widgets.
           Selects libraries and plays songs within them.

           print_side: Print to the panel widget
           nav_menu: Print and navigate directory entries.
           terminate: emergency thread terminate function
           print_items: print/draw items on curses widget/window
        """
        self.p = playsound()

        self.is_playing = False
        self.__running = True

        self.disp = disp
        self.meta = meta
        self.seek = seek
        self.menu = np.array(menu)  # list of items in current dir
        self.prev = np.array([])  # list of paths of previous menus
        self.list = np.array([])  # playlist/queue
        self.selected = 0  # selected item in menu
        # dtype: 2D numpy array data types; integer and string
        self.dtype = [('track', 'i4'), ('song', 'U500')]
        self.temp = "__play_temp.wav"
        self.q = 0  # queue index
        self.time = b_to_i(0)
        self.s_len = b_to_i(0)

    def is_audio(self, file):
        """
            Currently supported file types:
           '.mp3', '.flac' and '.wav'
        """
        if file.endswith(('.mp3', '.flac', '.wav',)):
            return True
        return False

    def back(self):
        level_1, self.prev = self.prev[-1], self.prev[:-1]
        self.menu = getdir(1, level_1)
        self.selected = 0
        self.print_items()

    def print_seek(self, total_len):
        """
            Print to the seek widget
        """
        self.seek.clear()

        song_len = b_to_i(total_len)
        self.time = b_to_i(int(self.p.get_position()))
        seek_str = "{0} / {1}".format(self.time, song_len)
        x_pos = self.seek.getmaxyx()[1] - len(seek_str) - 1

        self.seek.addstr(0, x_pos, seek_str)
        self.seek.refresh()

    def print_side(self):
        """
            Print to the panel (left-most) widget.
        """

        self.meta.clear()

        p_len = self.meta.getmaxyx()[1] - 1  # printable length in window
        playlist = [TinyTag.get(song[1]).title for song in self.list]
        album = TinyTag.get(self.list[0][1]).album
        artist = TinyTag.get(self.list[0][1]).artist

        # header: artist - album
        self.meta.addnstr(1, 1, "{0} - {1}".format(artist, album), p_len)
        self.meta.hline(2, 1, '-', p_len)  # h-line: -----------
        # songs in album
        for i in range(len(playlist)):
            if i == self.q:
                self.meta.attron(color_pair(1))
            self.meta.addnstr(i + 3, 1, playlist[i], p_len)
            self.meta.attroff(color_pair(1))
            self.meta.addstr('\n')

        self.meta.refresh()

    def print_items(self):
        """
            Prompt curses to print each entry in a given menu
            on the main panel.
        """

        self.disp.clear()
        self.disp.box()

        for i, item in enumerate(self.menu):
            if i == self.selected:
                self.disp.attron(color_pair(1))
            self.disp.addstr(i + 1, 1, item.name)
            self.disp.attroff(color_pair(1))

        self.disp.refresh()

    def previous(self):
        """
            Play the previous song in queue (Lumen.list)
        """
        try:
            if self.q > 0:
                self.q -= 1
                self.play(self.temp)
                self.print_items()
        except Exception:
            print(Exception)

    def next(self):
        """
            Play the next song in queue (Lumen.list)
        """
        try:
            if self.q < len(self.list) - 1:
                self.q += 1
                self.play(self.temp)
                self.print_items()
        except Exception:
            print(Exception)

    def stop(self):
        """
            Stop song currently playing
        """
        try:
            if self.p.get_status() in ['playing', 'paused']:
                self.p.stop()
                self.p.close_alias()
                if dir_exists(self.temp):
                    i_del(self.temp)
                self.print_items()
        except Exception:
            print("No song in queue to stop")
            pass

    def play_bytes():
        pass

    def play(self, temp=""):
        """
            Play the (Lumen.q)th song from the given (menu).

            If a (temp) file
            is given and exists then it will delete it before it
            is used again for the next (Lumen.q)th song.
        """

        if temp and dir_exists(temp):
            if self.is_playing:
                try:
                    self.p.stop()
                    self.p.close_alias()
                except Exception:
                    pass
            i_del(temp)

        song = self.list[self.q][1]

        if song.endswith(('.flac')):
            with open(song, 'rb') as f:
                data, file_stream = sf.read(f)
                sf.write(temp, data, file_stream)
            del(data)
            del(file_stream)
            self.p.play(temp, False)

        else:
            self.p.play(song, False)

        self.s_len = int(self.p.get_duration_of_audio())
        self.is_playing = True
        self.print_side()

    def quit(self):
        self.stop()
        self.terminate()

    def nav_menu(self, key):
        """
            Logic and actions for directory items.

            Handles selecting items and running them
            (if they are audio files)

            key: keycode of the last key pressed

        """
        file = self.menu[self.selected]
        enter_pressed = (key == KEY_ENTER or key in [10, 13])

        if key == KEY_UP and self.selected > 0:
            self.selected -= 1
            self.print_items()
        if key == KEY_DOWN and self.selected < len(self.menu) - 1:
            self.selected += 1
            self.print_items()

        if enter_pressed:
            if file.is_dir():
                """ if this is a directory/folder, open it """
                self.prev = np.append(  # get parent directory and add to tree
                    self.prev, [getpardir(self.menu[0].path)])
                sel_path = file.path  # path of selected folder
                self.menu = getdir(seek=1, wdir=sel_path)
                self.selected = 0
                self.print_items()

            elif file.is_file():
                playlist = [
                    song.path for song in self.menu if self.is_audio(song.path)]
                idex = [(int(TinyTag.get(song).track) - 1)  # track number
                        for song in playlist]
                self.list = np.array(  # make a numbered track list
                    list(zip(idex, playlist)), dtype=self.dtype)
                # sort this track list
                self.list = np.sort(self.list, order='track')

                try:
                    """ try to get the song's tag, els """
                    self.q = int(TinyTag.get(file.path).track) - 1
                except Exception:
                    print("No ID3 found for {}".format(file.path))
                    self.q = self.selected
                self.play(self.temp)

        if key == ord('p'):
            if self.p.get_status() == 'playing':
                self.p.pause()
            elif self.p.get_status() == 'paused':
                self.p.resume(False)

        if key == ord('q'):
            self.back()

        self.print_items()
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
        self.print_items()
        while self.__running:
            try:
                self.print_seek(self.s_len)
                if self.list is not None:
                    if self.p.get_status() == "stopped":
                        self.next()
                    if self.list[-1] == self.list[self.q]:
                        # if this is the last song in playlist
                        self.list = np.array([])  # empty playlist
            except Exception:
                self.seek.clear()
                x_pos = self.seek.getmaxyx()[1] - len(self.time)
                self.seek.addstr(0, x_pos - 1, self.time)
                self.seek.refresh()

            key = self.disp.getch()
            if is_pressed('ctrl + comma'):
                self.previous()
                continue

            if is_pressed('ctrl + period'):
                self.next()
                continue

            if is_pressed('ctrl + q'):
                self.quit()
                continue

            if is_pressed('ctrl + s'):
                self.stop()
                self.time = b_to_i(0)
                continue

            # if is_pressed('alt + left'):
            #     self.back()
                # continue

            self.nav_menu(key)

        if dir_exists(self.temp):
            i_del(self.temp)
