#!/usr/bin/env python3

import sys
import platform
import pprint
import logzero
import os
import re
from logzero import logger as log

from spotdl import __version__
from spotdl import const
from spotdl import handle
from spotdl import internals
from spotdl import spotify_tools
from spotdl import metadata

def debug_sys_info():
    log.debug("Python version: {}".format(sys.version))
    log.debug("Platform: {}".format(platform.platform()))
    log.debug(pprint.pformat(const.args.__dict__))



def main():
    const.args = handle.get_arguments()
    logzero.setup_default_logger(formatter=const._formatter, level=const.args.log_level)

    file = const.args.file
    
    if file is not None:
        search = re.sub(".mp3", "", file)
        md = spotify_tools.generate_metadata(search)
        metadata.embed(file, md)
    else:
        files = os.listdir(".")
        files = list(filter(lambda x: re.search(r'^[^.]', x), files))
        files = list(filter(lambda x: re.search(r'my-free-mp3', x), files))
        for file in files:
            search = re.sub(" my-free-mp3s.com.*", "", file)
            name = search + ".mp3"
            os.rename(file, name)
            md = spotify_tools.generate_metadata(search)
            metadata.embed(name, md)


    try:
        True#match_args()
        # actually we don't necessarily need this, but yeah...
        # explicit is better than implicit!
        #sys.exit(0)
    except KeyboardInterrupt as e:
        log.exception(e)
        sys.exit(3)


if __name__ == "__main__":
    main()
