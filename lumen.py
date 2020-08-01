from libs.playsound.playsound import playsound
from time import sleep
from keyboard import is_pressed
class player:

    def __init__(self, *arugments, **keywords):
        self.__running = True
        self.music_player = playsound()

    def run(self, song, block=False):
        self.music_player.play(song, block)
        while self.__running:
            sleep(0.1)
            if is_pressed('ctrl+q'):
                self.music_player.stop()
                self.__running = False
            if is_pressed('p'):
                if self.music_player.get_status() == 'playing':
                    self.music_player.pause()
                    continue
                self.music_player.resume(False)
