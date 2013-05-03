CREATE TABLE posts (
	added INTEGER DEFAULT (strftime('%s', 'now')),
	rating TEXT,
	mime TEXT,
	key BLOB
)
