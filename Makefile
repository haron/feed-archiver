URLS ?= ~/.newsboat/urls
export PYTHONWARNINGS=ignore
export DYLD_LIBRARY_PATH="$(shell echo $$(brew --prefix)/opt/sqlite3/lib:$$DYLD_LIBRARY_PATH)"

help:
	@./archiver.py -h

fetch: fix-db
	@./archiver.py --strip-html < $(URLS)

web:
	uv tool run --with datasette-sqlite-vec --with sqlite-vec --with datasette-embeddings datasette rss.db --metadata metadata.yaml

stats:
	@sqlite3 rss.db "select 'feeds', count(*) from feed_metadata; select 'entries', count(*) from feed_entries"

linter: githooks
	uv tool run black --line-length 120 *.py
	uv tool run flake8 --config ~/.flake8 *.py

safety:
	uv tool run safety check -o bare

githooks:
	git config --local core.hooksPath .githooks

fix-db:
	@sqlite3 rss.db .dump | sqlite3 rss2.db && mv rss2.db rss.db && rm -rf rss.db-journal
