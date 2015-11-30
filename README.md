# Overview

This webapplication serves the following purpose:

* Provides a file and directory browser
* Generates a m3u8 playlist for media files
* Serves transcoded chunks of the media files as they are referenced in the m3u8 file

The chunking is done using ffmpeg's `-ss` and `-t` option.
This doesn't work properly on some video files.

Also with some files we get chrome errors about audio-splicing with can lead to the point where the browser suddenly
stops playback.

# Compatibility

The video stream is encoded as h.264 + AAC stream. Tested with

* Google Chrome / Chromium
* Android Stock "Browser"

# Requirements

* python3, flask
* `ffmpeg` command
* `ffmpegthumbnailer` command

# Run tests

    python3 -m unittest test

# Run with WSGI

(here with waitress)

    waitress-serve --port 8000 mediabrowser.wsgi:application
