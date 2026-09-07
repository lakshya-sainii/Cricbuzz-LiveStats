USE CricbuzzLiveStats;
GO

-- =========================================================
-- 1. Total number of teams
-- =========================================================
SELECT COUNT(*) AS TotalTeams
FROM teams;
GO


-- =========================================================
-- 2. Total number of players
-- =========================================================
SELECT COUNT(*) AS TotalPlayers
FROM players;
GO


-- =========================================================
-- 3. Total number of matches
-- =========================================================
SELECT COUNT(*) AS TotalMatches
FROM matches;
GO


-- =========================================================
-- 4. Total number of series
-- =========================================================
SELECT COUNT(*) AS TotalSeries
FROM series;
GO


-- =========================================================
-- 5. Total number of venues
-- =========================================================
SELECT COUNT(*) AS TotalVenues
FROM venues;
GO


-- =========================================================
-- 6. Top 10 run scorers
-- =========================================================
SELECT TOP 10
    p.player_id,
    p.player_name,
    SUM(pms.runs) AS TotalRuns
FROM player_match_stats pms
JOIN players p
    ON pms.player_id = p.player_id
GROUP BY
    p.player_id,
    p.player_name
ORDER BY TotalRuns DESC;
GO


-- =========================================================
-- 7. Top 10 wicket takers
-- =========================================================
SELECT TOP 10
    p.player_id,
    p.player_name,
    SUM(pms.wickets) AS TotalWickets
FROM player_match_stats pms
JOIN players p
    ON pms.player_id = p.player_id
GROUP BY
    p.player_id,
    p.player_name
ORDER BY TotalWickets DESC;
GO


-- =========================================================
-- 8. Top 10 players with most sixes
-- =========================================================
SELECT TOP 10
    p.player_name,
    SUM(pms.sixes) AS TotalSixes
FROM player_match_stats pms
JOIN players p
    ON pms.player_id = p.player_id
GROUP BY p.player_name
ORDER BY TotalSixes DESC;
GO


-- =========================================================
-- 9. Top 10 players with most fours
-- =========================================================
SELECT TOP 10
    p.player_name,
    SUM(pms.fours) AS TotalFours
FROM player_match_stats pms
JOIN players p
    ON pms.player_id = p.player_id
GROUP BY p.player_name
ORDER BY TotalFours DESC;
GO


-- =========================================================
-- 10. Highest individual batting scores
-- =========================================================
SELECT TOP 10
    p.player_name,
    pms.runs,
    pms.balls_faced,
    pms.match_id
FROM player_match_stats pms
JOIN players p
    ON pms.player_id = p.player_id
ORDER BY pms.runs DESC;
GO


-- =========================================================
-- 11. Best bowling performances in a match
-- =========================================================
SELECT TOP 10
    p.player_name,
    pms.wickets,
    pms.runs_conceded,
    pms.overs,
    pms.match_id
FROM player_match_stats pms
JOIN players p
    ON pms.player_id = p.player_id
WHERE pms.overs > 0
ORDER BY
    pms.wickets DESC,
    pms.runs_conceded ASC;
GO


-- =========================================================
-- 12. Player batting strike rate
-- Minimum 50 balls faced
-- =========================================================
SELECT TOP 10
    p.player_name,
    SUM(pms.runs) AS TotalRuns,
    SUM(pms.balls_faced) AS TotalBalls,
    CAST(
        SUM(pms.runs) * 100.0 /
        NULLIF(SUM(pms.balls_faced), 0)
        AS DECIMAL(10,2)
    ) AS StrikeRate
FROM player_match_stats pms
JOIN players p
    ON pms.player_id = p.player_id
GROUP BY p.player_name
HAVING SUM(pms.balls_faced) >= 50
ORDER BY StrikeRate DESC;
GO


-- =========================================================
-- 13. Players with most matches recorded
-- =========================================================
SELECT TOP 10
    p.player_name,
    COUNT(DISTINCT pms.match_id) AS MatchesPlayed
FROM player_match_stats pms
JOIN players p
    ON pms.player_id = p.player_id
GROUP BY p.player_name
ORDER BY MatchesPlayed DESC;
GO


-- =========================================================
-- 14. Average runs per match by player
-- Minimum 5 matches
-- =========================================================
SELECT TOP 10
    p.player_name,
    COUNT(DISTINCT pms.match_id) AS MatchesPlayed,
    SUM(pms.runs) AS TotalRuns,
    CAST(
        SUM(pms.runs) * 1.0 /
        COUNT(DISTINCT pms.match_id)
        AS DECIMAL(10,2)
    ) AS AverageRunsPerMatch
FROM player_match_stats pms
JOIN players p
    ON pms.player_id = p.player_id
GROUP BY p.player_name
HAVING COUNT(DISTINCT pms.match_id) >= 5
ORDER BY AverageRunsPerMatch DESC;
GO


-- =========================================================
-- 15. Players with both runs and wickets
-- All-round performance
-- =========================================================
SELECT TOP 10
    p.player_name,
    SUM(pms.runs) AS TotalRuns,
    SUM(pms.wickets) AS TotalWickets
FROM player_match_stats pms
JOIN players p
    ON pms.player_id = p.player_id
GROUP BY p.player_name
HAVING
    SUM(pms.runs) > 0
    AND SUM(pms.wickets) > 0
ORDER BY
    TotalRuns DESC,
    TotalWickets DESC;
GO


-- =========================================================
-- 16. Number of matches played by each team
-- =========================================================
SELECT
    t.team_name,
    COUNT(*) AS MatchesPlayed
FROM teams t
JOIN matches m
    ON t.team_id = m.team1_id
    OR t.team_id = m.team2_id
GROUP BY t.team_name
ORDER BY MatchesPlayed DESC;
GO


-- =========================================================
-- 17. Matches played at each venue
-- =========================================================
SELECT
    v.venue_name,
    v.city,
    COUNT(m.match_id) AS TotalMatches
FROM venues v
LEFT JOIN matches m
    ON v.venue_id = m.venue_id
GROUP BY
    v.venue_name,
    v.city
ORDER BY TotalMatches DESC;
GO


-- =========================================================
-- 18. Series with the most matches
-- =========================================================
SELECT
    s.series_name,
    COUNT(m.match_id) AS TotalMatches
FROM series s
LEFT JOIN matches m
    ON s.series_id = m.series_id
GROUP BY s.series_name
ORDER BY TotalMatches DESC;
GO


-- =========================================================
-- 19. Match format distribution
-- =========================================================
SELECT
    match_format,
    COUNT(*) AS TotalMatches
FROM matches
GROUP BY match_format
ORDER BY TotalMatches DESC;
GO


-- =========================================================
-- 20. Most recent 20 matches
-- =========================================================
SELECT TOP 20
    m.match_id,
    t1.team_name AS Team1,
    t2.team_name AS Team2,
    m.match_date,
    m.match_format,
    m.status
FROM matches m
LEFT JOIN teams t1
    ON m.team1_id = t1.team_id
LEFT JOIN teams t2
    ON m.team2_id = t2.team_id
ORDER BY m.match_date DESC;
GO


-- =========================================================
-- 21. Matches with team scores
-- =========================================================
SELECT TOP 20
    m.match_id,
    t1.team_name AS Team1,
    m.team1_score,
    t2.team_name AS Team2,
    m.team2_score,
    m.status
FROM matches m
LEFT JOIN teams t1
    ON m.team1_id = t1.team_id
LEFT JOIN teams t2
    ON m.team2_id = t2.team_id
WHERE
    m.team1_score IS NOT NULL
    OR m.team2_score IS NOT NULL
ORDER BY m.match_date DESC;
GO


-- =========================================================
-- 22. Team-wise total player runs
-- =========================================================
SELECT
    t.team_name,
    SUM(pms.runs) AS TotalRuns
FROM player_match_stats pms
JOIN teams t
    ON pms.team_id = t.team_id
GROUP BY t.team_name
ORDER BY TotalRuns DESC;
GO


-- =========================================================
-- 23. Team-wise total wickets
-- =========================================================
SELECT
    t.team_name,
    SUM(pms.wickets) AS TotalWickets
FROM player_match_stats pms
JOIN teams t
    ON pms.team_id = t.team_id
GROUP BY t.team_name
ORDER BY TotalWickets DESC;
GO


-- =========================================================
-- 24. Players scoring 50 or more runs in a match
-- =========================================================
SELECT
    p.player_name,
    pms.runs,
    pms.balls_faced,
    pms.fours,
    pms.sixes,
    pms.match_id
FROM player_match_stats pms
JOIN players p
    ON pms.player_id = p.player_id
WHERE pms.runs >= 50
ORDER BY pms.runs DESC;
GO


-- =========================================================
-- 25. Best all-round performances in a single match
-- Player scored 30+ runs and took at least 2 wickets
-- =========================================================
SELECT
    p.player_name,
    pms.match_id,
    pms.runs,
    pms.wickets,
    pms.runs_conceded
FROM player_match_stats pms
JOIN players p
    ON pms.player_id = p.player_id
WHERE
    pms.runs >= 30
    AND pms.wickets >= 2
ORDER BY
    pms.runs DESC,
    pms.wickets DESC;
GO