-- LEVEL 6: SUBQUERIES & ADVANCED FILTERING (IN / NOT IN)
--
-- Yesterday we talked about how a LEFT JOIN can be slow on a Billion-row dataset 
-- if you are just trying to filter out missing data.
-- Today, we are learning the Hyper-Optimized way to do it using Subqueries!

-- PART 1: THE 'IN' and 'NOT IN' OPERATOR
-- Instead of using a bunch of OR statements (genre = 'Rock' OR genre = 'Pop' OR genre = 'Jazz'),
-- you can just provide a list!
-- 
-- Example: 
-- SELECT * FROM streaming_history WHERE artist_name IN ('LiSA', 'Eminem', 'Aimer');


-- PART 2: THE SUBQUERY (A query inside a query)
-- What if you don't know the exact list of artists off the top of your head? 
-- What if you want to say: "Give me all the songs by artists who have a 'J-Pop' genre in the other table"?
--
-- You can write a SELECT statement INSIDE the IN() parentheses! 
-- 
-- Example:
-- SELECT song_name 
-- FROM streaming_history 
-- WHERE artist_name IN (
--      SELECT artist_name FROM artist_genres WHERE genre = 'J-Pop'
-- );
--
-- Notice how the inner query runs FIRST, generates a list of names, and then passes 
-- that list to the outer query! This is often much faster than a JOIN.


-- ==========================================
-- QUESTION 1 (The Subquery Optimization)
-- ==========================================
-- Write a query to find all 'song_name's in the 'streaming_history' table 
-- where the 'artist_name' is NOT IN the 'artist_genres' table. 
--
-- (This is the highly optimized, Subquery version of LeetCode #183!)
