# Overview

This webapplication serves the following purpose:

* Provides a file and directory browser
* Generates a m3u8 playlist for media files
* Serves transcoded chunks of the media files as they are referenced in the m3u8 file

The chunking is done using ffmpeg's `-ss` and `-t` option.
This doesn't work properly on some video files.

## Compatibility

The video stream is encoded as MPEG4-AVC video and AAC audio stream. That works in:

* Google Chrome / Chromium
* Android Stock "Browser"
* Firefox with Media Source Extension (MSE), thus supporting h264/aac
* [Kodi plugin](kodi-mediabrowser/)

## Requirements

* python3, flask
* `ffmpeg` command

## Run tests

    python3 -m unittest test

## Run with WSGI

(here with waitress)

    waitress-serve --port 8000 mediabrowser.wsgi:application
