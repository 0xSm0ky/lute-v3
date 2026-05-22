-- Add a 0..5 rating column to books.  NULL = no rating set.
ALTER TABLE books ADD COLUMN BkRating INTEGER NULL;
