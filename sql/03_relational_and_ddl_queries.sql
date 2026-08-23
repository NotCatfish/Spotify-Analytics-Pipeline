-- LEVEL 3: RELATIONAL DATA & DDL (JOINs, CREATE, DROP)
--
-- Data Analysts mostly read data (SELECT), but they also need to know how to create 
-- temporary tables and join them together.

-- PART 1: DDL (Data Definition Language) & DML (Data Manipulation Language)

-- QUESTION 1 (CREATE TABLE)
-- Let's pretend you are analyzing your Spotify data and you want to categorize your top artists.
-- Write a query to CREATE a new table named 'artist_genres'. 
-- It should have two columns: 'artist_name' (VARCHAR) and 'genre' (VARCHAR).


-- QUESTION 2 (INSERT)
-- Write an INSERT statement to add the following 3 rows into your new 'artist_genres' table:
-- 1. 'LiSA', 'J-Pop'
-- 2. 'Eminem', 'Hip-Hop'
-- 3. 'RADWIMPS', 'Rock'


-- QUESTION 3 (UPDATE)
-- You made a mistake! RADWIMPS is actually 'J-Rock', not just 'Rock'.
-- Write an UPDATE statement to change the genre to 'J-Rock' WHERE the artist_name is 'RADWIMPS'.


-- PART 2: JOINS

-- QUESTION 4 (INNER JOIN)
-- Join your new 'artist_genres' table with the main 'streaming_history' table.
-- Write a query that shows the artist_name, genre, and song_name. 
-- Only show rows where the artist exists in BOTH tables (which is what INNER JOIN does).


-- QUESTION 5 (LEFT JOIN)
-- Now write the exact same query, but use a LEFT JOIN (putting streaming_history on the left).
-- Notice how the artists that are NOT in your genre table (like 'milet' or '樹海') still show up, 
-- but their genre column says NULL!


-- QUESTION 6 (JOIN with Aggregation)
-- Using an INNER JOIN between streaming_history and artist_genres, calculate the total sec_played FOR EACH GENRE.
-- (You want to group by genre, and sum the sec_played).


-- PART 3: CLEANUP

-- QUESTION 7 (TRUNCATE)
-- TRUNCATE deletes all the data inside a table, but leaves the empty table structure intact.
-- Write a query to TRUNCATE your 'artist_genres' table.


-- QUESTION 8 (DROP)
-- DROP deletes the entire table completely from the database.
-- Write a query to DROP your 'artist_genres' table.
