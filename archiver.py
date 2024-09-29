#!/usr/bin/env -S uv run -q
import os
import sys
import logging
import configargparse
import feedparser
import concurrent.futures
import sqlean as sqlite3
import strip_tags


def fetch_rss(feed_url):
    logging.debug(f"Fetching {feed_url}")
    feed = feedparser.parse(feed_url)
    return feed


def preprocess(text):
    if text and args.strip_html:
        text = strip_tags.strip_tags(text)
    return text


def save_feed(feed, cursor):
    cursor.execute(
        """
        INSERT INTO feed_metadata (title, link, description)
        VALUES (?, ?, ?)
        ON CONFLICT(link) DO UPDATE SET
        title=excluded.title,
        description=excluded.description
        RETURNING id
    """,
        (feed.feed.get("title"), feed.feed.get("link"), feed.feed.get("description")),
    )
    feed_id = cursor.fetchone()[0]

    for entry in feed.entries:
        cursor.execute(
            """
            INSERT INTO feed_entries (feed_id, title, link, published, summary)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(feed_id, link) DO UPDATE SET
            title=excluded.title,
            published=excluded.published,
            summary=excluded.summary
        """,
            (
                feed_id,
                preprocess(entry.get("title")),
                entry.get("link"),
                entry.get("published"),
                preprocess(entry.get("summary")),
            ),
        )


def create_db(cursor):
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS feed_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            title TEXT,
            link TEXT,
            description TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_feed_metadata_unique ON feed_metadata (link);
        CREATE TABLE IF NOT EXISTS feed_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            feed_id INTEGER,
            title TEXT,
            link TEXT,
            published TEXT,
            summary TEXT,
            FOREIGN KEY(feed_id) REFERENCES feed_metadata(id)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_feed_entries_unique ON feed_entries (feed_id, link);
        CREATE TRIGGER IF NOT EXISTS feed_metadata_updated_at
                AFTER INSERT ON feed_entries
                BEGIN
                    UPDATE feed_metadata
                    SET updated_at=(SELECT max(created_at) FROM feed_entries WHERE feed_id=NEW.feed_id)
                    WHERE id=NEW.feed_id;
                END;
        -- SELECT load_extension('lembed0');
        -- SELECT load_extension('vec0');
    """
    )


def main(feed_urls):
    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()

    if args.sql_debug:
        conn.set_trace_callback(print)

    create_db(cursor)

    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        for feed in executor.map(fetch_rss, feed_urls):
            save_feed(feed, cursor)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    parser = configargparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--debug",
        env_var="DEBUG",
        action="store_true",
        help="Enable debug mode to print fetching URLs",
    )
    parser.add_argument(
        "--db",
        default="rss.db",
        help="Database file name (default: rss.db)",
    )
    parser.add_argument(
        "--sql-debug",
        env_var="SQL_DEBUG",
        action="store_true",
        help="Enable SQL debug mode to print SQL statements",
    )
    parser.add_argument(
        "--strip-html",
        action="store_true",
        help="Strip HTML tags from entries",
    )
    parser.add_argument("feed_urls", nargs="*", help="List of feed URLs", default=[])

    args = parser.parse_args()

    feed_urls = args.feed_urls + os.environ.get("FEED_URLS", "").split()

    if not sys.stdin.isatty():
        feed_urls += [line.split("#", 1)[0].strip() for line in sys.stdin if line.split("#", 1)[0].strip()]

    logging.basicConfig(
        level=logging.DEBUG if args.debug or args.sql_debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if args.sql_debug:
        logging.info("SQL debugging enabled")

    if not feed_urls:
        logging.error("No feed URLs provided.")
        sys.exit(1)

    main(feed_urls)
