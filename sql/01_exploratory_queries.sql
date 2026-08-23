-- THE MERCARI DATA ANALYST SQL BOOTCAMP
-- Table: streaming_history
-- Type your SQL query directly below each question. Reply "done" in the chat when you have finished all of them!

-- QUESTION 1 (Level: Basic SELECT)
-- Write a query to select the song_name, artist_name, and platform from the streaming_history table. Limit the results to 15 rows so it doesn't crash your screen.
SELECT
    song_name,
    artist_name,
    platform
FROM streaming_history
LIMIT 15;


-- QUESTION 2 (Level: WHERE Filter)
-- Write a query to find all songs you played on the 'Android' platform (or whatever your phone platform is called). Show only the song_name and artist_name.
SELECT
    song_name,
    artist_name
FROM streaming_history
WHERE platform='Android'
LIMIT 10;


-- QUESTION 3 (Level: Multiple Filters)
-- Write a query to find all songs by 'LiSA' that were played for more than 120 seconds (sec_played > 120). Show song_name and sec_played.
SELECT
    song_name,
    sec_played
FROM streaming_history
WHERE sec_played>120 AND artist_name='LiSA';


-- QUESTION 4 (Level: Basic Aggregation)
-- How many times have you listened to the artist 'RADWIMPS' in total? (Your output should just be a single column with a single number).
SELECT
    count(CASE WHEN artist_name='RADWIMPS' THEN 1 END)
FROM streaming_history;

-- QUESTION 5 (Level: GROUP BY)
-- Write a query to find out how many total seconds you have spent listening to EACH artist. Show the artist_name and the SUM of sec_played.
SELECT
    artist_name,
    sum(sec_played)
FROM streaming_history
GROUP BY artist_name;

-- QUESTION 6 (Level: ORDER BY and LIMIT)
-- Who are your Top 10 most listened-to artists based on the total NUMBER OF TIMES you played their songs? Show the artist_name and the play count, ordered highest to lowest.
SELECT
    artist_name,
    COUNT(song_name)
FROM streaming_history
GROUP BY artist_name
ORDER BY count(song_name) DESC;

-- QUESTION 7 (Level: Multiple GROUP BY)
-- Write a query to see how many times you used each platform to listen to each artist. Show artist_name, platform, and the count of plays.
SELECT
    platform,
    artist_name,
    COUNT(song_name)
FROM streaming_history
GROUP BY artist_name,platform
ORDER BY count(song_name) DESC, platform DESC;

-- QUESTION 8 (Level: Conditional Aggregation / Pivot)
-- For each artist, count how many times you played them with incognito_mode = 1, and how many times with incognito_mode = 0. Show artist_name and the two count columns. (Hint: Use CASE WHEN inside the COUNT).
SELECT
    artist_name,
    COUNT(CASE WHEN incognito_mode=1 THEN 1 END) AS incognito,
    COUNT(CASE WHEN incognito_mode=0 THEN 1 END) AS non_incognito
FROM streaming_history
GROUP BY artist_name;

-- QUESTION 9 (Level: Basic Window Function)
-- Rank your entire streaming history from longest play (sec_played) to shortest play. Show the song_name, sec_played, and the rank. (Hint: Do not use GROUP BY).
SELECT
    song_name,
    sec_played,
    RANK() OVER (ORDER BY song_name ASC,sec_played DESC )
FROM streaming_history;

-- QUESTION 10 (Level: Partitioned Window Function)
-- Show the artist_name, song_name, and sec_played for every song. Add a column that ranks the length of the play (sec_played) from longest to shortest, but RESET the rank for each different PLATFORM.
SELECT
    RANK() OVER (partition by platform ORDER BY sec_played desc,artist_name ASC),
    platform,
    artist_name,
    song_name,
    sec_played
FROM streaming_history;