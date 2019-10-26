import spotipy
import spotipy.oauth2 as oauth2

from slugify import slugify
from titlecase import titlecase
from logzero import logger as log
import pprint
import sys
import os
import functools

from spotdl import const
from spotdl import internals

spotify = None


def generate_token():
    """ Generate the token. """
    credentials = oauth2.SpotifyClientCredentials(
        client_id="4fe3fecfe5334023a1472516cc99d805",
        client_secret="0f02b7c483c04257984695007a4a8d5c",
    )
    token = credentials.get_access_token()
    return token


def must_be_authorized(func, spotify=spotify):
    def wrapper(*args, **kwargs):
        global spotify
        try:
            assert spotify
            return func(*args, **kwargs)
        except (AssertionError, spotipy.client.SpotifyException):
            token = generate_token()
            spotify = spotipy.Spotify(auth=token)
            return func(*args, **kwargs)

    return wrapper


@must_be_authorized
def generate_metadata(raw_song):
    """ Fetch a song's metadata from Spotify. """
    if internals.is_spotify(raw_song):
        # fetch track information directly if it is spotify link
        log.debug("Fetching metadata for given track URL")
        meta_tags = spotify.track(raw_song)
    else:
        # otherwise search on spotify and fetch information from first result
        log.debug('Searching for "{}" on Spotify'.format(raw_song))
        try:
            meta_tags = spotify.search(raw_song, limit=1)["tracks"]["items"][0]
        except IndexError:
            return None
    artist = spotify.artist(meta_tags["artists"][0]["id"])
    album = spotify.album(meta_tags["album"]["id"])

    try:
        meta_tags[u"genre"] = titlecase(artist["genres"][0])
    except IndexError:
        meta_tags[u"genre"] = None
    try:
        meta_tags[u"copyright"] = album["copyrights"][0]["text"]
    except IndexError:
        meta_tags[u"copyright"] = None
    try:
        meta_tags[u"external_ids"][u"isrc"]
    except KeyError:
        meta_tags[u"external_ids"][u"isrc"] = None

    meta_tags[u"release_date"] = album["release_date"]
    meta_tags[u"publisher"] = album["label"]
    meta_tags[u"total_tracks"] = album["tracks"]["total"]

    log.debug("Fetching lyrics")
    meta_tags["lyrics"] = None

    # Some sugar
    meta_tags["year"], *_ = meta_tags["release_date"].split("-")
    meta_tags["duration"] = meta_tags["duration_ms"] / 1000.0
    meta_tags["spotify_metadata"] = True
    # Remove unwanted parameters
    del meta_tags["duration_ms"]
    del meta_tags["available_markets"]
    del meta_tags["album"]["available_markets"]

    log.debug(pprint.pformat(meta_tags))
    return meta_tags
