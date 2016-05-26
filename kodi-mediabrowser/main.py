#!/usr/bin/env python3
#  -*- coding: utf-8 -*-
# Module: default
import sys
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
from urllib import quote
import logging

logging.basicConfig(level=logging.INFO)

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

addon = xbmcaddon.Addon()

endpoint = addon.getSetting('endpoint')


def list_files(path):
    resp = requests.get(endpoint + path)
    data = resp.json()
    files = data['files']

    listing = []
    for file in files:
        list_item = xbmcgui.ListItem(label=file['name'])

        if file['type'] == 'directory':
            list_item.setInfo('video', {'title': file['name'] + '/'})
            url = '{0}?action=list_files&path={1}'.format(_url, quote(file['path']))
            listing.append((url, list_item, True))
        else:
            list_item.setInfo('video', {'title': file['name']})
            list_item.setArt({'thumb': endpoint + file['poster']})
            list_item.setProperty('IsPlayable', 'true')
            url = endpoint + file['m3u8']
            listing.append((url, list_item, False))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'list_files':
            # Display the list of videos in a provided category.
            list_videos(params['path'])
        else:
            raise Exception('Invalid params')
    else:
        list_files('/json/')


if __name__ == '__main__':
    router(sys.argv[2][1:])
