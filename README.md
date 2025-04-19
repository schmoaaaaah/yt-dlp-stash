This repository contains a stash plugin package for [yt-dlp](https://github.com/yt-dlp/yt-dlp#readme). 

See [yt-dlp plugins](https://github.com/yt-dlp/yt-dlp#plugins) for more details.

## Installation

Requires yt-dlp as well as stashapp-tools.

You can install this package with pip:

```bash
python3 -m pip install -U https://github.com/schmoaaaaah/yt-dlp-stash/archive/master.zip
python3 -m pip install yt-dlp-stash
```

See [installing yt-dlp plugins](https://github.com/yt-dlp/yt-dlp#installing-plugins) for the other methods this plugin package can be installed.

## Usage

To use this plugin, you must have a stash server running and add following to your yt-dlp command:

```bash
--use-postprocessor Stash:scheme="http"\;host="stash"\;port="9999"\;apikey="example_key"
```

The apikey is optional and can be left out if you dont have authentication enabled.

```bash
--use-postprocessor Stash:scheme="http"\;host="stash"\;port="9999"
```

### Variables

|name|default|required|description|
|---|---|---|---|
|scheme|http|x|scheme at which stash is available. either http or https|
|host|localhost|x|fqdn of the stash instance|
|port|9999|x|port on which stash is accessable|
|apikey|||api key which should be used
|sessioncookie|||sessioncookie which should be used|
|[searchpathoverride](#searchpathoverride)|||override the relative path for the search in stash|
|[scrapemethod](#scrapemethod)|yt_dlp|---|postprocessor scraping method, either yt_dlp or stash|

#### apikey & sessioncookie

if api key and **sessioncookie** are provided api key is preferred.

#### searchpathoverride

when the start of the absolute media path equals searchpathoverride the searchpathoverride is removed from the absolute media path and the rest of the path is used to search in stash.

```bash
searchpathoverride = /media/series
media_path = /media/series/series_name/season_1/episode_1.mkv
searchpath = /series_name/season_1/episode_1.mkv
```

when the start of the absolute media path __does not__ equal searchpathoverride it is used as a prefix for the search in stash.

```bash
searchpathoverride = /media/series
media_path = /series_name/season_1/episode_1.mkv
searchpath = /media/series/series_name/season_1/episode_1.mkv
```

when the searchpathoverride is not set the absolute media path is used to search in stash.

#### scrapemethod

With `yt_dlp` the postprocessor uses data directly from yt-dlp. Using `stash` triggers Stash's GraphQL to scrape the URL after import. (Note: you must install any [CommunityScrapers](https://github.com/stashapp/CommunityScrapers) you plan to use within Stash first for this to work properly)

## Development

See the [Plugin Development](https://github.com/yt-dlp/yt-dlp/wiki/Plugin-Development) section of the yt-dlp wiki.
