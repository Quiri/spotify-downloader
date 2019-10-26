from logzero import logger as log
import os
import sys
import math
import urllib.request


from spotdl import const

try:
    import winreg
except ImportError:
    pass

try:
    from slugify import SLUG_OK, slugify
except ImportError:
    log.error("Oops! `unicode-slugify` was not found.")
    log.info("Please remove any other slugify library and install `unicode-slugify`")
    sys.exit(5)

formats = {
    0: "track_name",
    1: "artist",
    2: "album",
    3: "album_artist",
    4: "genre",
    5: "disc_number",
    6: "duration",
    7: "year",
    8: "original_date",
    9: "track_number",
    10: "total_tracks",
    11: "isrc",
    12: "track_id",
}


def input_link(links):
    """ Let the user input a choice. """
    while True:
        try:
            log.info("Choose your number:")
            the_chosen_one = int(input("> "))
            if 1 <= the_chosen_one <= len(links):
                return links[the_chosen_one - 1]
            elif the_chosen_one == 0:
                return None
            else:
                log.warning("Choose a valid number!")
        except ValueError:
            log.warning("Choose a valid number!")



def is_spotify(raw_song):
    """ Check if the input song is a Spotify link. """
    status = len(raw_song) == 22 and raw_song.replace(" ", "%20") == raw_song
    status = status or raw_song.find("spotify") > -1
    return status


def format_string(
    string_format, tags, slugification=False, force_spaces=False, total_songs=0
):
    """ Generate a string of the format '[artist] - [song]' for the given spotify song. """
    format_tags = dict(formats)
    format_tags[0] = tags["name"]
    format_tags[1] = tags["artists"][0]["name"]
    format_tags[2] = tags["album"]["name"]
    format_tags[3] = tags["artists"][0]["name"]
    format_tags[4] = tags["genre"]
    format_tags[5] = tags["disc_number"]
    format_tags[6] = tags["duration"]
    format_tags[7] = tags["year"]
    format_tags[8] = tags["release_date"]
    format_tags[9] = tags["track_number"]
    format_tags[10] = tags["total_tracks"]
    format_tags[11] = tags["external_ids"]["isrc"]
    format_tags[12] = tags["id"]

    format_tags_sanitized = {
        k: sanitize_title(str(v), ok="'-_()[]{}") if slugification else str(v)
        for k, v in format_tags.items()
    }
    # calculating total digits presnet in total_songs to prepare a zfill.
    total_digits = 0 if total_songs == 0 else int(math.log10(total_songs)) + 1

    for x in formats:
        format_tag = "{" + formats[x] + "}"
        # Making consistent track number by prepending zero
        # on it according to number of digits in total songs
        if format_tag == "{track_number}":
            format_tags_sanitized[x] = format_tags_sanitized[x].zfill(total_digits)

        string_format = string_format.replace(format_tag, format_tags_sanitized[x])

    if const.args.no_spaces and not force_spaces:
        string_format = string_format.replace(" ", "_")

    return string_format


def sanitize_title(title, ok="-_()[]{}"):
    """ Generate filename of the song to be downloaded. """

    if const.args.no_spaces:
        title = title.replace(" ", "_")

    # replace slashes with "-" to avoid folder creation errors
    title = title.replace("/", "-").replace("\\", "-")

    # slugify removes any special characters
    title = slugify(title, ok=ok, lower=False, spaces=True)
    return title


def filter_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
    for temp in os.listdir(path):
        if temp.endswith(".temp"):
            os.remove(os.path.join(path, temp))


def videotime_from_seconds(time):
    if time < 60:
        return str(time)
    if time < 3600:
        return "{0}:{1:02}".format(time // 60, time % 60)

    return "{0}:{1:02}:{2:02}".format((time // 60) // 60, (time // 60) % 60, time % 60)


def get_sec(time_str):
    if ":" in time_str:
        splitter = ":"
    elif "." in time_str:
        splitter = "."
    else:
        raise ValueError(
            "No expected character found in {} to split" "time values.".format(time_str)
        )
    v = time_str.split(splitter, 3)
    v.reverse()
    sec = 0
    if len(v) > 0:  # seconds
        sec += int(v[0])
    if len(v) > 1:  # minutes
        sec += int(v[1]) * 60
    if len(v) > 2:  # hours
        sec += int(v[2]) * 3600
    return sec


def extract_spotify_id(raw_string):
    """
    Returns a Spotify ID of a playlist, album, etc. after extracting
    it from a given HTTP URL or Spotify URI.
    """

    if "/" in raw_string:
        # Input string is an HTTP URL
        if raw_string.endswith("/"):
            raw_string = raw_string[:-1]
        # We need to manually trim additional text from HTTP URLs
        # We could skip this if https://github.com/plamere/spotipy/pull/324
        # gets merged,
        to_trim = raw_string.find("?")
        if not to_trim == -1:
            raw_string = raw_string[:to_trim]
        splits = raw_string.split("/")
    else:
        # Input string is a Spotify URI
        splits = raw_string.split(":")

    spotify_id = splits[-1]

    return spotify_id



def content_available(url):
    try:
        response = urllib.request.urlopen(url)
    except urllib.request.HTTPError:
        return False
    else:
        return response.getcode() < 300
