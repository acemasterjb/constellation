# constellation
Minimalistic, lightweight MP3, WAVE and FLAC music player. A TUI front end for this [playsound](https://github.com/Zehina/playsound) fork.

This project is in alpha stages but you can try by installing the dependency, cloning the project and running the main python script.

FLAC files are converted to WAVE files via [simpleaudio](https://github.com/hamiltron/py-simple-audio) then playback is handled by playsound.

## dependencies
eyeD3 - to show MP3 metadata on info panel
```
	pip install eyeD3
```

## instructions

Install dependencies, clone this project and run main.py

```
	~/> python main.py
```

You will be prompted to choose your music through the file browser, press `Enter` to choose a directory.

Press `Enter` to play a song, `p` to pause and resume playback and `ctrl+q` to stop and exit program.

If you would like to go up a directory level, press `q`.


## current state
This project is a WIP. Currently, you can browse a directory once chossen, play and pause a song, and stop it.

~~Currently working on how to properly pause and resume.~~

~~Currently working on how to navigate while playing music~~

~~Currently working on segmenting tui window into widgets~~

Currently working on Seek Bar, seeking, packaging for executable

# Mission
- To create a lightweight music play that can be ran in the terminal/cmd window
- To provide support for a variety of containers
- To provide a seamless TUI music player experience for windows (though, this is meant to be crossplatform)
