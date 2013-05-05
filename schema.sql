CREATE TABLE posts (
	id INTEGER PRIMARY KEY,
	added TEXT DEFAULT CURRENT_TIMESTAMP,
	rating TEXT,
	mime TEXT,
	key TEXT
);

CREATE TABLE tags (
	id INTEGER PRIMARY KEY,
	name TEXT,
	type TEXT
);

CREATE TABLE posts_tags (
	pid INTEGER,
	tid INTEGER,
	FOREIGN KEY(pid) REFERENCES posts(id) ON DELETE CASCADE,
	FOREIGN KEY(tid) REFERENCES tags(id) ON DELETE CASCADE,
	# Because we don't want any post to appear twice in one tag
	# Use REPLACE just in case we add any other columns to the
	# mapping table in the future.
	UNIQUE(pid, tid) ON CONFLICT REPLACE
);

# Watch the mapping table for deletions (rather than the post
# table; cascades will make post deletions reflect on the
# mapping table as well) and clear out any tags that no longer
# have any references to them.
CREATE TRIGGER clear_empty_tags AFTER DELETE ON posts_tags
BEGIN
	DELETE FROM tags WHERE id NOT IN (SELECT tid FROM posts_tags);
END;
