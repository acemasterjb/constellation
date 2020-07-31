from libs.playsound.playsound import playsound
from time import sleep
from curses import KEY_ENTER

class player:

    def __init__(self, *arugments, **keywords):
        self.__running = True
        self.paused = False
        # self.resume = False

    def stop(self):
        self.__running = False

    def pause(self, c):
        self.paused = True
        c.acquire()

    def resume(self, c):
        self.paused = False
        c.notify()
        c.release()

    def run(self, disp, song, e, c):
        music_player = playsound()
        music_player.play(song, block=False)
        e.set()
        # song_position = None

        while self.__running:
            sleep(0.1)
            # key = disp.getch()
            # is_enter = (key == KEY_ENTER or key in [10, 13])
            # if key == ord('q') or is_enter:
            #     music_player.stop()
            #     self.stop()
            with c:
                while self.paused:
                    music_player.pause()
                    c.wait()
                # if self.resume:
                #     music_player.resume()
                #     self.resume = False
            # if key == ord('p'):
            #     if music_player.get_status() == 'paused':
            #         music_player.play(song, block=False, pos=song_position)
            #         song_position = None
            #         disp.clear()
            #         disp.refresh()
            #     else:
            #         song_position = music_player.get_position()
            #         music_player.stop()
                # print(pos)
