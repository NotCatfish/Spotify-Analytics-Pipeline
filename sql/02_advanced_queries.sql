-- LEVEL 2: ADVANCED SQL DRILLS
-- Table: streaming_history

-- QUESTION 1 (Math & Aggregation)
-- Find the total number of HOURS (not seconds) you spent listening to 'Eminem' in 'incognito_mode'. (Hint: Divide the sum of sec_played by 3600).
SELECT
    artist_name,
    SUM(sec_played)/3600 AS hours_played
FROM streaming_history
WHERE incognito_mode=0 AND artist_name='Eminem'
GROUP BY artist_name;

-- QUESTION 2 (Grouping by Multiple Columns)
-- Which specific album by 'RADWIMPS' have you listened to the most (by total play count)? Show artist, album, and play count.
SELECT
    artist_name,
    album_name,
    COUNT(song_name) AS play_count
FROM streaming_history
WHERE artist_name='RADWIMPS'
GROUP BY artist_name,album_name
ORDER BY play_count DESC;

-- QUESTION 3 (Pivot Table - Platform Analysis)
-- Pick 3 of your favorite artists. Show the artist_name, and use Conditional Aggregation (CASE WHEN) to create 3 new columns: plays on 'Android', plays on 'Windows', and plays on 'Web Player (Browser)'.
SELECT
    artist_name,
    COUNT(CASE WHEN platform LIKE '%android%' THEN 1 END) AS andriod_plays,
    COUNT(CASE WHEN platform LIKE '%windows%' THEN 1 END) AS windows_plays,
    COUNT(CASE WHEN platform LIKE '%linux%' THEN 1 END) AS linux_plays
FROM streaming_history
WHERE artist_name IN ('樹海', 'Lilas Ikuta', 'milet')
GROUP BY artist_name;

-- QUESTION 4 (Advanced Pivot - Start Reason)
-- Let's look at how songs start. Group by artist_name. Count how many times a song started because of 'trackdone' (meaning you let the previous song finish naturally) vs 'fwdbtn' (meaning you clicked the skip button to get to it). 
SELECT
    artist_name,
    COUNT(CASE WHEN reason_start='trackdone' THEN 1 END) AS trackdone_count,
    COUNT(CASE WHEN reason_start='fwdbtn' THEN 1 END) AS fwdbtn_count
FROM streaming_history
GROUP BY artist_name
ORDER BY artist_name ASC;

-- QUESTION 5 (Basic CTE)
-- Build a CTE called 'skip_data' that calculates the total skips (where skipped = 1) for each song_name. Then, write a main query that selects from 'skip_data' to show ONLY songs with more than 50 skips.
WITH skip_data AS(
    SELECT
        song_name,
        SUM(skipped) as skip_count
    FROM streaming_history
    GROUP BY song_name
)
SELECT
    song_name,
    skip_count
FROM skip_data
WHERE skip_count>50
ORDER BY skip_count ASC;

-- QUESTION 6 (CTE + Math)
-- Build a CTE that calculates the total_plays and total_skips for each artist. In your main query, select from that CTE and calculate their "Skip Rate" (total_skips divided by total_plays).
WITH total_info AS(
    SELECT
        artist_name,
        COUNT(CASE WHEN skipped=1 THEN 1 END) as total_skips,
        COUNT(song_name) as total_plays
    FROM streaming_history
    GROUP BY artist_name
)
SELECT
    artist_name,
    CAST(total_skips AS FLOAT)/total_plays AS skip_ratio
FROM total_info
ORDER BY 2 DESC;


-- QUESTION 7 (Window Function - No CTE)
-- Rank every individual time you listened to 'LiSA' from longest session to shortest session. Show song_name, sec_played, and the rank.
SELECT
    RANK() OVER (ORDER BY sec_played DESC),
    song_name,
    sec_played
FROM streaming_history
WHERE artist_name='LiSA';

-- QUESTION 8 (CTE + Window Function)
-- Build a CTE to calculate the total sec_played for each album. Then, query that CTE to rank the albums from most-played to least-played overall.
WITH total_sec_played_album AS(
    SELECT
        artist_name,
        album_name,
        SUM(sec_played) AS total_sec_played
    FROM streaming_history
    GROUP BY artist_name,album_name
)

SELECT
    RANK() OVER (ORDER BY total_sec_played DESC),
    album_name,
    artist_name,
    total_sec_played
FROM total_sec_played_album;

-- QUESTION 9 (CTE + Window Function with Partition)
-- Build a CTE to find the total play count for every artist AND song combination. In the main query, rank the songs FOR EACH ARTIST from most played to least played.
WITH all_combo as(
    SELECT
        artist_name,
        song_name,
        COUNT(song_name) as play_counts
    FROM streaming_history
    GROUP BY artist_name,song_name
)

SELECT
    RANK() OVER (PARTITION BY artist_name ORDER BY play_counts DESC),
    artist_name,
    song_name,
    play_counts
FROM all_combo
GROUP BY artist_name,song_name,play_counts
ORDER BY artist_name ASC,play_counts DESC;

-- QUESTION 10 (Filtering a Window Function - The True Final Boss)
-- Golden Rule: You cannot put a Window Function in a WHERE clause!
-- Using the exact same code from Question 9, wrap it in ONE MORE CTE (you can chain CTEs using a comma) so that you can filter the final results to show ONLY the #1 most played song for every artist!
WITH all_combo as(
    SELECT
        artist_name,
        song_name,
        COUNT(song_name) as play_counts
    FROM streaming_history
    GROUP BY artist_name,song_name
    ORDER BY artist_name ASC, play_counts DESC
),
filtered_data AS(
    SELECT
        artist_name,
        song_name,
        RANK() OVER (PARTITION BY artist_name ORDER BY play_counts DESC) AS song_rank
    FROM all_combo
)

SELECT
    artist_name,
    song_name,
    play_counts
FROM filtered_data
WHERE song_rank=1;