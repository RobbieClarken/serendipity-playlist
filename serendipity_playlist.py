#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Add songs from Spotify's "Serendipity" web site to a playlist.
Usage: ./serendipity_playlist.py [username] [playlist_name]
"""

import spotipy
import spotipy.util
import requests


def get_serendipity_tracks():

    """
    Get the track ids of the songs in the Spotify Serendipity web app.
    """

    url = 'https://www.spotify.com/au/arts/serendipity/data/cache.json'
    return [t.split('\t')[0] for t in requests.get(url).json()]


def response_generator(response):

    """
    Keep yielding responses to a Spotify query until there are no more.
    """

    yield response
    while response['next']:
        response = sp.next(response)
        yield response


def get_playlist_id(sp, username, playlist_name):

    """
    Find a Spotify user's playlist by name. If it doesn't exist, create it.
    """

    for response in response_generator(sp.user_playlists(username)):
        playlist = find_by_key_value(response['items'], 'name', playlist_name)
        if playlist:
            break
    else:
        playlist = sp.user_playlist_create(username, playlist_name)

    return playlist['id']


def get_playlist_track_ids(sp, username, playlist_id):

    """ Get the track id of every song on a playlist. """

    playlist_responses = response_generator(
        sp.user_playlist_tracks(username, playlist_id, fields='next,items')
    )
    track_ids = []
    for response in playlist_responses:
        track_ids += [item['track']['id'] for item in response['items']]

    return track_ids


def add_tracks(sp, username, playlist_id, tracks):

    """ Add tracks to the user's playlist. """

    limit = 50 # The Spotify API only allows 50 tracks to be added at a time.
    for i in range(0, len(tracks), limit):
        sp.user_playlist_add_tracks(username, playlist_id, tracks[i:i+limit])


def find_by_key_value(dicts, key, value, default=None):

    """ Find the first dict object in a list where obj[key] = value. """

    return next((d for d in dicts if key in d and d[key] == value), default)


if __name__ == '__main__':

    import sys
    from argparse import ArgumentParser

    parser = ArgumentParser(description=('Create a playlist with songs from '
                                         'Spotify\'s Serendipity web app.'))
    parser.add_argument('username', nargs='?', help='Spotify username')
    parser.add_argument('playlist_name', nargs='?', default='Serendipity',
                        help='Playlist name')
    args = parser.parse_args()

    username = args.username or raw_input('Spotify Username: ')
    playlist_name = args.playlist_name

    token = spotipy.util.prompt_for_user_token(username,
                                               scope='playlist-modify-public')
    if not token:
        sys.exit('Could not get Spotify token.')
    sp = spotipy.Spotify(auth=token)

    playlist_id = get_playlist_id(sp, username, playlist_name)
    current_tracks = get_playlist_track_ids(sp, username, playlist_id)
    new_tracks = get_serendipity_tracks()

    # Remove duplicates and tracks already on the playlist.
    new_tracks = list(set(new_tracks) - set(current_tracks))
    add_tracks(sp, username, playlist_id, new_tracks)

    print('{} new tracks added to {}.'.format(len(new_tracks), playlist_name))
