from curses import color_pair, KEY_ENTER, KEY_UP, KEY_DOWN
from libs.playsound.playsound import playsound
from keyboard import is_pressed
from time import sleep
from tinytag import TinyTag
import soundfile as sf
from .quark import getdir, dir_exists, i_del
# from.seek import Seek
# from threading import Timer


class Lumen():
    """
       Class for file browser and data panel widgets.
       Selects libraries and plays songs within them.

       print_data: Print to the panel widget
       nav_menu: Print and navigate directory entries.
       terminate: emergency thread terminate function
       print_items: print/draw items on curses widget/window
    """

    def __init__(self, disp, meta, seek, menu, selected):
        self.p = playsound()
        # self.is_playing = self.p.get_status() == 'playing'
        # self.is_paused = self.p.get_status() == 'paused'
        self.__running = True

        self.disp = disp
        self.meta = meta
        self.seek = seek
        self.menu = menu
        self.selected = selected

    def is_audio(self, file):
        if file.endswith(('.mp3', '.flac',)):
            return True
        return False

    def print_data(self, disp, menu, selected):
        """
            Print to the panel (left-most) widget.
        """

        file = menu[selected].path

        if menu[selected].is_file():
            audio = TinyTag.get(file)
            # audio = eyed3.load(file)
            disp.clear()
            disp.box()

            song_name = audio.title
            artist = audio.artist
            album = audio.album

            metadata = [song_name, artist, album]

            for i in range(len(metadata) - 1):
                disp.addstr(i + 4, 1, metadata[i])
                disp.addstr('\n')

        else:
            disp.clear()

        disp.refresh()

    def terminate(self):
        """
            Terminate thread / shut down application
        """
        self.__running = False

    def print_items(self, disp, menu, selected):
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
                disp.attron(color_pair(1))
            disp.addstr(i + 1, 1, item.name)
            disp.attroff(color_pair(1))

        disp.refresh()

    def nav_menu(self, disp, meta, seek, menu, selected):
        """
            Logic and actions for directory items.

            Handles selecting items and running them
            (if they are audio files)
            disp: curses window
            menu: list of position: item pairs in a directory
            selected: position of cursor

        """

        self.print_items(disp, menu, 0)
        prev = [menu]

        while self.__running:
            key = disp.getch()
            is_enter = (key == KEY_ENTER or key in [10, 13])

            if key == KEY_UP and selected > 0:
                selected -= 1
                self.print_items(disp, menu, selected)
                if self.is_audio(menu[selected].path):
                    self.print_data(meta, menu, selected)
            if key == KEY_DOWN and selected < len(menu) - 1:
                selected += 1
                self.print_items(disp, menu, selected)
                if self.is_audio(menu[selected].path):
                    self.print_data(meta, menu, selected)

            if is_enter:
                if menu[selected].is_dir():
                    prev.append(menu)
                    sel_path = menu[selected].path
                    menu = getdir(1, sel_path)
                    selected = 0

                    self.print_items(disp, menu, selected)

                elif menu[selected].is_file():
                    playing = menu[selected].path

                    if menu[selected].path.endswith(('.flac')):
                        with open(playing, 'rb') as f:
                            data, file_stream = sf.read(f)
                            sf.write("__play_temp.wav", data, file_stream)
                        del(data)
                        del(file_stream)
                        self.p.play("__play_temp.wav", False)
                        # len_b = int(
                        # self.p.get_duration_of_audio().decode()) // 60

                    else:
                        self.p.play(playing, False)
                        # len_b = int(
                        # self.p.get_duration_of_audio().decode()) // 60

                    # seek_bar = Seek(self.p)
                    # seek_bar.run_seek(seek, menu, selected, len_b)
                    # seek_bar.run_seek(seek, menu, selected, len_b)
                    # t.start()

            if key == ord('s'):
                metadata = TinyTag.get(menu[selected].path)

                playlist = dirscanner(
                    dirname(menu[selected].path), check_album, metadata.album)

                for song in playlist:
                    self.p.play(song)

            if key == ord('p'):
                if self.p.get_status() == 'playing':
                    self.p.pause()
                elif self.p.get_status() == 'paused':
                    self.p.resume(False)
                else:
                    pass

            if is_pressed('ctrl+q'):
                if self.p.get_status() in ['playing', 'paused']:
                    self.p.stop()
                    self.p.close_alias()
                    if dir_exists("__play_temp.wav"):
                        i_del("__play_temp.wav")
                self.terminate()
                # break

            if is_pressed('ctrl+s'):
                try:
                    if self.p.get_status() in ['playing', 'paused']:
                        self.p.stop()
                        self.p.close_alias()
                        if dir_exists("__play_temp.wav"):
                            i_del("__play_temp.wav")
                except Exception:
                    pass

            if key == ord('q'):
                menu = prev.pop()
                self.print_items(disp, menu, 0)
            sleep(0.025)

        if dir_exists("__play_temp.wav"):
            i_del("__play_temp.wav")

    def run_player(self):
        self.nav_menu(self.disp, self.meta, self.seek,
                      self.menu, self.selected)
