from libs.playsound.playsound import playsound
from curses import KEY_ENTER

class player:

    def __init__(self, *arugments, **keywords):
        self.__running = True

    def stop(self):
        self.__running = False

    def run(self, disp, song):
        music_player = playsound()
        music_player.play(song, block=False)
        song_position = None

        while self.__running:
            key = disp.getch()
            is_enter = (key == KEY_ENTER or key in [10, 13])

            if key == ord('q') or is_enter:
                music_player.stop()
                self.stop()
            if key == ord('p'):
                if music_player.get_status() == 'paused':
                    music_player.play(song, block=False, pos=song_position)
                    song_position = None
                else:
                    song_position = music_player.get_position()
                    music_player.stop()
                # print(pos)
