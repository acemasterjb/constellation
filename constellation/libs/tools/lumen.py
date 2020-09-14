from curses import color_pair, KEY_ENTER, KEY_UP, KEY_DOWN
from libs.playsound.playsound import playsound
from keyboard import is_pressed
from time import sleep
from tinytag import TinyTag
import soundfile as sf
from .quark import getdir, dir_exists, i_del
# from string import printable
# from.seek import Seek
# from threading import Timer


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
        self.list = []
        self.selected = 0
        self.temp = "__play_temp.wav"
        self.q = 0

    def is_audio(self, file):
        if file.endswith(('.mp3', '.flac',)):
            return True
        return False

    # def nav_entry(self, direction, Q, n_items):
    #     if direction and Q < n_items - 1:
    #         Q += 1
    #     elif not direction and Q > 0:
    #         Q -= 1

    def print_side(self, disp, q=None):
        """
            Print to the panel (left-most) widget.
        """

        disp.clear()

        p_len = disp.getmaxyx()[1] - 1  # printable length in window
        playlist = [TinyTag.get(song).title for song in self.list]

        # album header
        disp.addnstr(1, 1, TinyTag.get(self.list[0]).album, p_len)
        disp.hline(2, 1, '-', p_len)  # h-line: -----------
        # songs in album
        for i in range(len(playlist)):
            if q and i == q:
                disp.attron(color_pair(1))
            disp.addnstr(i + 3, 1, playlist[i], p_len)
            disp.attroff(color_pair(1))
            disp.addstr('\n')

        # file = menu[self.selected].path

        # if menu[self.selected].is_file():
        #     audio = TinyTag.get(file)
        #     # audio = eyed3.load(file)
        #     disp.clear()
        #     disp.box()

        #     song_name = audio.title
        #     artist = audio.artist
        #     album = audio.album

        #     metadata = [song_name, artist, album]
        #     # j = 0

        #     for i in range(len(metadata)):
        #         # pos = 0
        #         # j += 1
        #         # for c in range(0, len(metadata[i])):
        #         #     if pos < disp.getmaxyx()[1]:
        #         #         disp.addch(j, pos, metadata[i][c])
        #         #         pos += 1
        #         #     else:
        #         #         disp.addstr('\n')
        #         #         j += 1
        #         #         pos = 1
        #         # disp.addstr('\n')
        #         disp.addstr(i + 4, 1, metadata[i])
        #         disp.addstr('\n')

        disp.refresh()

    def print_items(self, disp, menu):
        """
            Prompt curses to print each entry in a given menu.

            disp: curses window
            menu: list of position: item pairs in a directory
        """

        disp.clear()
        disp.box()

        for i, item in enumerate(menu):
            if i == self.selected:
                disp.attron(color_pair(1))
            disp.addstr(i + 1, 1, item.name)
            disp.attroff(color_pair(1))

        disp.refresh()

    def play(self, menu, selected, disp, temp=""):
        """
            Play the (selected) song from the given (menu).

            If a (temp) file
            is given and exists then it will delete it before it
            is used again for the next (selected) song.
        """
        if temp and dir_exists(temp):
            if self.is_playing:
                try:
                    self.p.stop()
                    self.p.close_alias()
                except Exception:
                    pass
            i_del(temp)

        playing = menu[selected].path

        if menu[selected].path.endswith(('.flac')):
            with open(playing, 'rb') as f:
                data, file_stream = sf.read(f)
                sf.write(temp, data, file_stream)
            del(data)
            del(file_stream)
            self.p.play(temp, False)

        else:
            self.p.play(playing, False)

        self.is_playing = True
        self.print_side(disp, self.q)

    def nav_menu(self, disp, meta, seek, menu):
        """
            Logic and actions for directory items.

            Handles selecting items and running them
            (if they are audio files)
            disp: curses window
            menu: list of position: item pairs in a directory

        """

        self.print_items(disp, menu)
        prev = [menu]

        while self.__running:
            key = disp.getch()
            is_enter = (key == KEY_ENTER or key in [10, 13])

            if key == KEY_UP and self.selected > 0:
                self.selected -= 1
                # self.nav_entry(0, self.selected, len(menu))
                self.print_items(disp, menu)
            if key == KEY_DOWN and self.selected < len(menu) - 1:
                self.selected += 1
                # self.nav_entry(1, self.selected, len(menu))
                self.print_items(disp, menu)

            if is_enter:
                if menu[self.selected].is_dir():
                    prev.append(menu)
                    sel_path = menu[self.selected].path
                    menu = getdir(1, sel_path)
                    self.selected = 0
                    self.print_items(disp, menu)

                elif menu[self.selected].is_file():
                    self.q = self.selected
                    self.list = [
                        song.path for song in menu if self.is_audio(song.path)]
                    self.play(menu, self.q, meta, self.temp)

            if key == ord('p'):
                if self.p.get_status() == 'playing':
                    self.p.pause()
                elif self.p.get_status() == 'paused':
                    self.p.resume(False)
                else:
                    pass

            if is_pressed('ctrl + comma'):
                try:
                    if self.q > 0:
                        self.q -= 1
                        # self.nav_entry(1, self.q, len(menu))
                        self.play(menu, self.q, meta, self.temp)
                except Exception:
                    pass

            if is_pressed('ctrl + period'):
                try:
                    if self.q < len(self.list) - 1:
                        self.q += 1
                        # self.nav_entry(1, self.q, len(menu))
                        self.play(menu, self.q, meta, self.temp)
                except Exception:
                    print(Exception)

            if is_pressed('ctrl+q'):
                if self.p.get_status() in ['playing', 'paused']:
                    self.p.stop()
                    self.p.close_alias()
                    if dir_exists(self.temp):
                        i_del(self.temp)
                self.terminate()
                # break

            if is_pressed('ctrl+s'):
                try:
                    if self.p.get_status() in ['playing', 'paused']:
                        self.p.stop()
                        self.p.close_alias()
                        if dir_exists(self.temp):
                            i_del(self.temp)
                except Exception:
                    pass

            if key == ord('q'):
                menu = prev.pop()
                self.selected = 0
                self.print_items(disp, menu)
            sleep(0.025)

        if dir_exists(self.temp):
            i_del(self.temp)

    def terminate(self):
        """
            Terminate thread / shut down application
        """
        self.__running = False

    def run_player(self):

        self.nav_menu(self.disp, self.meta, self.seek,
                      self.menu)
