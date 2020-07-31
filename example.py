# Thank you Zehina!
from libs.playsound.playsound import playsound
import keyboard
import time

music = r'https://vgmdownloads.com/soundtracks/pokemon-omega-ruby-and-alpha-sapphire-nintendo-3ds-gamerip/vsjuiabu/059%20-%20Lilycove%20City.mp3'
# music = 'file.mp3'

player = playsound()  # Initializing a player object

player.play(music, block=False)  # Start Playing audio from an url or file

while True:
    time.sleep(0.1)
    # Pause the player if the keys ctrl + p are pressed
    if keyboard.is_pressed('ctrl+p'):
        player.pause()
    # Resume the player if the keys ctrl + r are pressed
    if keyboard.is_pressed('ctrl+r'):
        player.resume(block=False)
