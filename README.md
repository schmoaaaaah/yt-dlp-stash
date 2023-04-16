This repository contains a stash plugin package for [yt-dlp](https://github.com/yt-dlp/yt-dlp#readme). 

See [yt-dlp plugins](https://github.com/yt-dlp/yt-dlp#plugins) for more details.


## Installation

Requires yt-dlp `2023.01.02` or above as well as stashapp-tools.

You can install this package with pip:
```shell
python3 -m pip install -U https://github.com/schmoaaaaah/yt-dlp-stash/archive/master.zip
```

See [installing yt-dlp plugins](https://github.com/yt-dlp/yt-dlp#installing-plugins) for the other methods this plugin package can be installed.


## Usage

To use this plugin, you must have a stash server running and add following to your yt-dlp command:
```shell
--use-postprocessor Stash:stashurl="http:stash:9999"\;when=after_video
```
You might need to change `after_video` to `playlist` if you are downloading a playlist.
I haven't tested this yet.

The Processor expects the same path for the media in stash as it is downloaded.

## Development

See the [Plugin Development](https://github.com/yt-dlp/yt-dlp/wiki/Plugin-Development) section of the yt-dlp wiki.
