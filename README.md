# RSS Feed Archiver

This program archives RSS feeds into a SQLite database. Then you can explore the archive
with [Datasette](https://datasette.io/) tool.

## Requirements

- `uv` command: see [Getting Started guide](https://docs.astral.sh/uv/#getting-started).
- (optional) `make` command: ensure it is installed on your system (usually it is).
- (optional) `sqlite3` command: `brew install sqlite` or equivalent.

## Usage

To fetch and archive RSS feeds, use `./archiver.py` command:

    > ./archiver.py -h
    usage: archiver.py [-h] [-d] [--db DB] [--sql-debug] [--strip-html] [feed_urls ...]

    positional arguments:
      feed_urls     List of feed URLs

    options:
      -h, --help    show this help message and exit
      -d, --debug   Enable debug mode to print fetching URLs [env var: DEBUG]
      --db DB       Database file name (default: rss.db)
      --sql-debug   Enable SQL debug mode to print SQL statements [env var: SQL_DEBUG]
      --strip-html  Strip HTML tags from entries

     In general, command-line values override environment variables which override defaults.

Alternatively, archiver can read URLs list from stdin and/or environment variable `FEED_URLS`:

    cat /path/to/urls.txt | FEED_URLS="https://feed1 https://feed2" ./archiver.py https://feed3 ...

## Example Crontab Entry

To run this program once a day, add the following line to your crontab file (`crontab -e` on Macos):

```cron
0 5 * * * cd /path/to/feed-archiver; ./archiver.py feed1 feed2 ...
```

## Browse the archive

Use `make web` command, then go to <http://127.0.0.1:8001>:

    > make web
    uv tool run --with datasette-sqlite-vec --with sqlite-vec datasette rss.db --metadata metadata.yaml
    INFO:     Started server process [98532]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
