from datetime import datetime
import time

from api.crickbuzz_client import CrickbuzzClient
from database.connection import get_connection


# ---------------------------------------------------------
# BASIC HELPERS
# ---------------------------------------------------------

def timestamp_to_datetime(timestamp):
    if not timestamp:
        return None

    return datetime.fromtimestamp(int(timestamp) / 1000)


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------
# TEAM
# ---------------------------------------------------------

def save_team(cursor, team):
    if not team:
        return None

    team_id = team.get("teamId")
    team_name = team.get("teamName")
    short_name = team.get("teamSName")

    if not team_id or not team_name:
        return None

    query = """
    IF EXISTS (
        SELECT 1
        FROM teams
        WHERE team_id = ?
    )
    BEGIN
        UPDATE teams
        SET team_name = ?,
            short_name = ?,
            updated_at = GETDATE()
        WHERE team_id = ?
    END
    ELSE
    BEGIN
        INSERT INTO teams (
            team_id,
            team_name,
            short_name
        )
        VALUES (?, ?, ?)
    END
    """

    cursor.execute(
        query,
        team_id,
        team_name,
        short_name,
        team_id,
        team_id,
        team_name,
        short_name
    )

    return team_id


# ---------------------------------------------------------
# SERIES
# ---------------------------------------------------------

def save_series(cursor, series_id, series_name):
    if not series_id:
        return

    if not series_name:
        series_name = "Unknown Series"

    query = """
    IF EXISTS (
        SELECT 1
        FROM series
        WHERE series_id = ?
    )
    BEGIN
        UPDATE series
        SET series_name = ?,
            updated_at = GETDATE()
        WHERE series_id = ?
    END
    ELSE
    BEGIN
        INSERT INTO series (
            series_id,
            series_name
        )
        VALUES (?, ?)
    END
    """

    cursor.execute(
        query,
        series_id,
        series_name,
        series_id,
        series_id,
        series_name
    )


# ---------------------------------------------------------
# VENUE
# ---------------------------------------------------------

def save_venue(cursor, venue):
    if not venue:
        return None

    venue_id = venue.get("id")
    venue_name = venue.get("ground")
    city = venue.get("city")

    if not venue_id:
        return None

    if not venue_name:
        venue_name = "Unknown Venue"

    query = """
    IF EXISTS (
        SELECT 1
        FROM venues
        WHERE venue_id = ?
    )
    BEGIN
        UPDATE venues
        SET venue_name = ?,
            city = ?,
            updated_at = GETDATE()
        WHERE venue_id = ?
    END
    ELSE
    BEGIN
        INSERT INTO venues (
            venue_id,
            venue_name,
            city
        )
        VALUES (?, ?, ?)
    END
    """

    cursor.execute(
        query,
        venue_id,
        venue_name,
        city,
        venue_id,
        venue_id,
        venue_name,
        city
    )

    return venue_id


# ---------------------------------------------------------
# MATCH
# ---------------------------------------------------------

def save_match(cursor, match_info):
    match_id = match_info.get("matchId")

    if not match_id:
        return

    series_id = match_info.get("seriesId")
    series_name = match_info.get("seriesName")

    team1 = match_info.get("team1", {})
    team2 = match_info.get("team2", {})
    venue = match_info.get("venueInfo", {})

    save_series(
        cursor,
        series_id,
        series_name
    )

    team1_id = save_team(cursor, team1)
    team2_id = save_team(cursor, team2)
    venue_id = save_venue(cursor, venue)

    match_date = timestamp_to_datetime(
        match_info.get("startDate")
    )

    match_format = match_info.get("matchFormat")
    status = match_info.get("status")

    query = """
    IF EXISTS (
        SELECT 1
        FROM matches
        WHERE match_id = ?
    )
    BEGIN
        UPDATE matches
        SET series_id = ?,
            team1_id = ?,
            team2_id = ?,
            venue_id = ?,
            match_date = ?,
            match_format = ?,
            status = ?,
            updated_at = GETDATE()
        WHERE match_id = ?
    END
    ELSE
    BEGIN
        INSERT INTO matches (
            match_id,
            series_id,
            team1_id,
            team2_id,
            venue_id,
            match_date,
            match_format,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    END
    """

    cursor.execute(
        query,

        match_id,

        series_id,
        team1_id,
        team2_id,
        venue_id,
        match_date,
        match_format,
        status,
        match_id,

        match_id,
        series_id,
        team1_id,
        team2_id,
        venue_id,
        match_date,
        match_format,
        status
    )


# ---------------------------------------------------------
# PROCESS LIVE / UPCOMING / RECENT MATCHES
# ---------------------------------------------------------

def process_match_data(data, source_name):
    conn = get_connection()
    cursor = conn.cursor()

    count = 0

    try:
        type_matches = data.get("typeMatches", [])

        for type_match in type_matches:

            series_matches = type_match.get(
                "seriesMatches",
                []
            )

            for series_item in series_matches:

                series_wrapper = series_item.get(
                    "seriesAdWrapper"
                )

                if not series_wrapper:
                    continue

                matches = series_wrapper.get(
                    "matches",
                    []
                )

                for match in matches:

                    match_info = match.get(
                        "matchInfo",
                        {}
                    )

                    if not match_info:
                        continue

                    save_match(
                        cursor,
                        match_info
                    )

                    count += 1

        conn.commit()

        print(
            f"{source_name}: "
            f"{count} matches saved successfully ✅"
        )

    except Exception as error:

        conn.rollback()

        print(
            f"{source_name} insert failed ❌"
        )

        print(error)

    finally:
        cursor.close()
        conn.close()


def load_all_matches():
    client = CrickbuzzClient()

    print("Fetching Live Matches...")
    process_match_data(
        client.get_live_matches(),
        "Live"
    )

    print("Fetching Upcoming Matches...")
    process_match_data(
        client.get_upcoming_matches(),
        "Upcoming"
    )

    print("Fetching Recent Matches...")
    process_match_data(
        client.get_recent_matches(),
        "Recent"
    )


# ---------------------------------------------------------
# PLAYER
# ---------------------------------------------------------

def save_player(
    cursor,
    player_id,
    player_name,
    team_id=None
):
    if not player_id or not player_name:
        return

    query = """
    IF EXISTS (
        SELECT 1
        FROM players
        WHERE player_id = ?
    )
    BEGIN
        UPDATE players
        SET player_name = ?,
            team_id = COALESCE(?, team_id),
            updated_at = GETDATE()
        WHERE player_id = ?
    END
    ELSE
    BEGIN
        INSERT INTO players (
            player_id,
            player_name,
            team_id
        )
        VALUES (?, ?, ?)
    END
    """

    cursor.execute(
        query,

        player_id,

        player_name,
        team_id,
        player_id,

        player_id,
        player_name,
        team_id
    )


# ---------------------------------------------------------
# FIND BOTH TEAMS OF A MATCH
# ---------------------------------------------------------

def get_match_teams(cursor, match_id):

    query = """
    SELECT
        m.team1_id,
        t1.team_name AS team1_name,
        t1.short_name AS team1_short,

        m.team2_id,
        t2.team_name AS team2_name,
        t2.short_name AS team2_short

    FROM matches m

    LEFT JOIN teams t1
        ON m.team1_id = t1.team_id

    LEFT JOIN teams t2
        ON m.team2_id = t2.team_id

    WHERE m.match_id = ?
    """

    cursor.execute(query, match_id)

    row = cursor.fetchone()

    if not row:
        return None

    return {
        "team1_id": row[0],
        "team1_name": row[1],
        "team1_short": row[2],

        "team2_id": row[3],
        "team2_name": row[4],
        "team2_short": row[5],
    }


# ---------------------------------------------------------
# IDENTIFY BATTING TEAM
# ---------------------------------------------------------

def identify_batting_team(
    match_teams,
    bat_team_name,
    bat_team_short
):

    if not match_teams:
        return None, None

    name = (bat_team_name or "").strip().lower()
    short = (bat_team_short or "").strip().lower()

    team1_name = (
        match_teams["team1_name"] or ""
    ).strip().lower()

    team1_short = (
        match_teams["team1_short"] or ""
    ).strip().lower()

    team2_name = (
        match_teams["team2_name"] or ""
    ).strip().lower()

    team2_short = (
        match_teams["team2_short"] or ""
    ).strip().lower()

    if name == team1_name or short == team1_short:

        return (
            match_teams["team1_id"],
            match_teams["team2_id"]
        )

    if name == team2_name or short == team2_short:

        return (
            match_teams["team2_id"],
            match_teams["team1_id"]
        )

    return None, None


# ---------------------------------------------------------
# PLAYER MATCH STATS UPSERT
# ---------------------------------------------------------

def save_player_stats(
    cursor,
    match_id,
    player_id,
    team_id,
    runs=None,
    balls=None,
    fours=None,
    sixes=None,
    wickets=None,
    overs=None,
    runs_conceded=None
):

    cursor.execute(
        """
        SELECT stat_id
        FROM player_match_stats
        WHERE match_id = ?
          AND player_id = ?
        """,
        match_id,
        player_id
    )

    existing = cursor.fetchone()

    if existing:

        query = """
        UPDATE player_match_stats

        SET team_id = COALESCE(?, team_id),

            runs =
                CASE
                    WHEN ? IS NOT NULL
                    THEN ?
                    ELSE runs
                END,

            balls_faced =
                CASE
                    WHEN ? IS NOT NULL
                    THEN ?
                    ELSE balls_faced
                END,

            fours =
                CASE
                    WHEN ? IS NOT NULL
                    THEN ?
                    ELSE fours
                END,

            sixes =
                CASE
                    WHEN ? IS NOT NULL
                    THEN ?
                    ELSE sixes
                END,

            wickets =
                CASE
                    WHEN ? IS NOT NULL
                    THEN ?
                    ELSE wickets
                END,

            overs =
                CASE
                    WHEN ? IS NOT NULL
                    THEN ?
                    ELSE overs
                END,

            runs_conceded =
                CASE
                    WHEN ? IS NOT NULL
                    THEN ?
                    ELSE runs_conceded
                END

        WHERE match_id = ?
          AND player_id = ?
        """

        cursor.execute(
            query,

            team_id,

            runs, runs,
            balls, balls,
            fours, fours,
            sixes, sixes,

            wickets, wickets,
            overs, overs,
            runs_conceded, runs_conceded,

            match_id,
            player_id
        )

    else:

        query = """
        INSERT INTO player_match_stats (
            match_id,
            player_id,
            team_id,
            runs,
            balls_faced,
            fours,
            sixes,
            wickets,
            overs,
            runs_conceded
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(
            query,

            match_id,
            player_id,
            team_id,

            runs or 0,
            balls or 0,
            fours or 0,
            sixes or 0,

            wickets or 0,
            overs or 0,
            runs_conceded or 0
        )


# ---------------------------------------------------------
# SAVE SCORECARD
# ---------------------------------------------------------

def save_scorecard(
    cursor,
    match_id,
    data
):

    innings_list = data.get(
        "scorecard",
        []
    )

    if not innings_list:
        return 0

    match_teams = get_match_teams(
        cursor,
        match_id
    )

    processed_players = set()

    for innings in innings_list:

        bat_team_name = innings.get(
            "batteamname"
        )

        bat_team_short = innings.get(
            "batteamsname"
        )

        batting_team_id, bowling_team_id = (
            identify_batting_team(
                match_teams,
                bat_team_name,
                bat_team_short
            )
        )

        # -----------------------------
        # UPDATE MATCH SCORE
        # -----------------------------

        innings_score = innings.get("score")
        innings_wickets = innings.get("wickets")
        innings_overs = innings.get("overs")

        if innings_score is not None:

            score_text = (
                f"{innings_score}/"
                f"{innings_wickets} "
                f"({innings_overs} ov)"
            )

            if (
                match_teams
                and batting_team_id
                == match_teams["team1_id"]
            ):

                cursor.execute(
                    """
                    UPDATE matches
                    SET team1_score = ?
                    WHERE match_id = ?
                    """,
                    score_text,
                    match_id
                )

            elif (
                match_teams
                and batting_team_id
                == match_teams["team2_id"]
            ):

                cursor.execute(
                    """
                    UPDATE matches
                    SET team2_score = ?
                    WHERE match_id = ?
                    """,
                    score_text,
                    match_id
                )

        # -----------------------------
        # BATSMEN
        # -----------------------------

        batsmen = innings.get(
            "batsman",
            []
        )

        for batsman in batsmen:

            player_id = batsman.get("id")
            player_name = batsman.get("name")

            if not player_id or not player_name:
                continue

            save_player(
                cursor,
                player_id,
                player_name,
                batting_team_id
            )

            save_player_stats(
                cursor=cursor,
                match_id=match_id,
                player_id=player_id,
                team_id=batting_team_id,

                runs=safe_int(
                    batsman.get("runs")
                ),

                balls=safe_int(
                    batsman.get("balls")
                ),

                fours=safe_int(
                    batsman.get("fours")
                ),

                sixes=safe_int(
                    batsman.get("sixes")
                )
            )

            processed_players.add(
                player_id
            )

        # -----------------------------
        # BOWLERS
        # -----------------------------

        bowlers = innings.get(
            "bowler",
            []
        )

        for bowler in bowlers:

            player_id = bowler.get("id")
            player_name = bowler.get("name")

            if not player_id or not player_name:
                continue

            save_player(
                cursor,
                player_id,
                player_name,
                bowling_team_id
            )

            save_player_stats(
                cursor=cursor,
                match_id=match_id,
                player_id=player_id,
                team_id=bowling_team_id,

                wickets=safe_int(
                    bowler.get("wickets")
                ),

                overs=safe_float(
                    bowler.get("overs")
                ),

                runs_conceded=safe_int(
                    bowler.get("runs")
                )
            )

            processed_players.add(
                player_id
            )

    return len(processed_players)


# ---------------------------------------------------------
# LOAD SCORECARDS FROM DATABASE MATCH IDS
# ---------------------------------------------------------

def load_scorecards(limit=5):

    client = CrickbuzzClient()

    conn = get_connection()
    cursor = conn.cursor()

    try:

        query = """
        SELECT TOP (?)
            match_id,
            status

        FROM matches

        WHERE status IS NOT NULL

          AND status NOT LIKE 'Match starts%'

          AND status NOT LIKE '%delayed%'

        ORDER BY match_date DESC
        """

        cursor.execute(
            query,
            limit
        )

        matches = cursor.fetchall()

        if not matches:

            print(
                "No completed matches found."
            )
            return

        successful = 0

        for row in matches:

            match_id = row[0]

            print(
                f"Fetching scorecard "
                f"for Match ID {match_id}..."
            )

            try:

                data = client.get_match_scorecard(
                    match_id
                )

                if not data.get("scorecard"):

                    print(
                        f"{match_id}: "
                        f"No scorecard available ⚠️"
                    )

                    continue

                player_count = save_scorecard(
                    cursor,
                    match_id,
                    data
                )

                conn.commit()

                successful += 1

                print(
                    f"{match_id}: "
                    f"{player_count} players "
                    f"saved ✅"
                )

                # Small pause between API calls
                time.sleep(0.5)

            except Exception as error:

                conn.rollback()

                print(
                    f"{match_id}: "
                    f"Scorecard failed ❌"
                )

                print(error)

        print()
        print(
            f"{successful} scorecards "
            f"saved successfully ✅"
        )

    finally:

        cursor.close()
        conn.close()



# ---------------------------------------------------------
# PLAYER PROFILE / COUNTRY ENRICHMENT
# ---------------------------------------------------------

def _find_first_value(data, candidate_keys):
    """
    Recursively search a nested API response and return the first
    non-empty value whose key matches one of candidate_keys.
    """
    wanted = {str(key).lower() for key in candidate_keys}

    if isinstance(data, dict):
        # Check direct keys first.
        for key, value in data.items():
            if str(key).lower() in wanted:
                if value is not None and str(value).strip():
                    return str(value).strip()

        # Then search nested objects.
        for value in data.values():
            result = _find_first_value(value, candidate_keys)
            if result:
                return result

    elif isinstance(data, list):
        for item in data:
            result = _find_first_value(item, candidate_keys)
            if result:
                return result

    return None


def extract_player_profile_fields(data):
    """
    Extract profile fields from the player-details API response.
    The recursive lookup makes this tolerant to small response-shape
    differences between API versions.
    """
    country = _find_first_value(
        data,
        [
            "intlTeam",
            "country",
            "countryName",
            "nationality",
        ],
    )

    role = _find_first_value(
        data,
        [
            "role",
            "playingRole",
            "playerRole",
        ],
    )

    batting_style = _find_first_value(
        data,
        [
            "bat",
            "battingStyle",
            "batStyle",
            "batting_style",
        ],
    )

    bowling_style = _find_first_value(
        data,
        [
            "bowl",
            "bowlingStyle",
            "bowlStyle",
            "bowling_style",
        ],
    )

    return {
        "country": country,
        "role": role,
        "batting_style": batting_style,
        "bowling_style": bowling_style,
    }


def enrich_team_countries_from_players():
    """
    Populate teams.country from the most common known player country
    for that team. Existing team-country values are preserved.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        ;WITH CountryCounts AS (
            SELECT
                p.team_id,
                LTRIM(RTRIM(p.country)) AS country,
                COUNT(*) AS player_count,
                ROW_NUMBER() OVER (
                    PARTITION BY p.team_id
                    ORDER BY COUNT(*) DESC, LTRIM(RTRIM(p.country))
                ) AS rn
            FROM players p
            WHERE p.team_id IS NOT NULL
              AND p.country IS NOT NULL
              AND LTRIM(RTRIM(p.country)) <> ''
            GROUP BY
                p.team_id,
                LTRIM(RTRIM(p.country))
        )
        UPDATE t
        SET
            t.country = cc.country,
            t.updated_at = GETDATE()
        FROM teams t
        JOIN CountryCounts cc
            ON t.team_id = cc.team_id
           AND cc.rn = 1
        WHERE t.country IS NULL
           OR LTRIM(RTRIM(t.country)) = '';
        """

        cursor.execute(query)
        updated = cursor.rowcount
        conn.commit()

        print(
            f"Team-country enrichment complete: "
            f"{max(updated, 0)} team records updated ✅"
        )

    except Exception as error:
        conn.rollback()
        print("Team-country enrichment failed ❌")
        print(error)

    finally:
        cursor.close()
        conn.close()


def enrich_player_profiles(limit=50, delay_seconds=1.2):
    """
    Fetch profile details only for players with missing profile fields.

    A small batch + delay is intentional because the RapidAPI Basic
    plan can return HTTP 429 when too many requests are sent quickly.
    """
    client = CrickbuzzClient()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT TOP (?)
                player_id,
                player_name
            FROM players
            WHERE country IS NULL
               OR LTRIM(RTRIM(country)) = ''
               OR role IS NULL
               OR LTRIM(RTRIM(role)) = ''
               OR batting_style IS NULL
               OR LTRIM(RTRIM(batting_style)) = ''
               OR bowling_style IS NULL
               OR LTRIM(RTRIM(bowling_style)) = ''
            ORDER BY player_id
            """,
            limit,
        )

        players = cursor.fetchall()

        if not players:
            print("No players need profile enrichment ✅")
            enrich_team_countries_from_players()
            return

        print(
            f"Starting profile enrichment for "
            f"{len(players)} players..."
        )

        successful = 0
        updated = 0
        rate_limited = 0

        for index, row in enumerate(players, start=1):
            player_id = row[0]
            player_name = row[1]

            print(
                f"[{index}/{len(players)}] "
                f"Fetching {player_name} "
                f"(ID {player_id})..."
            )

            try:
                data = client.get_player_details(player_id)
                fields = extract_player_profile_fields(data)

                successful += 1

                if not any(fields.values()):
                    print(
                        "  Profile fetched, but no usable "
                        "country/role/style fields found ⚠️"
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE players
                        SET
                            country =
                                CASE
                                    WHEN country IS NULL
                                      OR LTRIM(RTRIM(country)) = ''
                                    THEN ?
                                    ELSE country
                                END,

                            role =
                                CASE
                                    WHEN role IS NULL
                                      OR LTRIM(RTRIM(role)) = ''
                                    THEN ?
                                    ELSE role
                                END,

                            batting_style =
                                CASE
                                    WHEN batting_style IS NULL
                                      OR LTRIM(RTRIM(batting_style)) = ''
                                    THEN ?
                                    ELSE batting_style
                                END,

                            bowling_style =
                                CASE
                                    WHEN bowling_style IS NULL
                                      OR LTRIM(RTRIM(bowling_style)) = ''
                                    THEN ?
                                    ELSE bowling_style
                                END,

                            updated_at = GETDATE()

                        WHERE player_id = ?
                        """,
                        fields["country"],
                        fields["role"],
                        fields["batting_style"],
                        fields["bowling_style"],
                        player_id,
                    )

                    conn.commit()
                    updated += 1

                    print(
                        "  Saved:",
                        f"country={fields['country'] or '-'},",
                        f"role={fields['role'] or '-'},",
                        f"bat={fields['batting_style'] or '-'},",
                        f"bowl={fields['bowling_style'] or '-'} ✅",
                    )

                time.sleep(delay_seconds)

            except Exception as error:
                conn.rollback()

                error_text = str(error)

                if "429" in error_text or "Too Many Requests" in error_text:
                    rate_limited += 1

                    print(
                        "  API rate limit reached (429) ⚠️"
                    )
                    print(
                        "  Stopping this batch safely. "
                        "Run the command again later."
                    )
                    break

                print(
                    f"  Player profile failed ❌: "
                    f"{error}"
                )

                # Pause a little even after a normal API failure.
                time.sleep(delay_seconds)

        print()
        print("----------------------------------------")
        print("PLAYER PROFILE ENRICHMENT SUMMARY")
        print("----------------------------------------")
        print(f"API profiles fetched : {successful}")
        print(f"Players updated      : {updated}")
        print(f"Rate-limit stops     : {rate_limited}")

        # Once player countries exist, derive country values for teams.
        enrich_team_countries_from_players()

    finally:
        cursor.close()
        conn.close()


def show_country_enrichment_status():
    """
    Print a quick database status so you can verify that the
    World Cricket Map now has country data to display.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_players,
                SUM(
                    CASE
                        WHEN country IS NOT NULL
                         AND LTRIM(RTRIM(country)) <> ''
                        THEN 1 ELSE 0
                    END
                ) AS players_with_country
            FROM players
            """
        )

        player_row = cursor.fetchone()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_teams,
                SUM(
                    CASE
                        WHEN country IS NOT NULL
                         AND LTRIM(RTRIM(country)) <> ''
                        THEN 1 ELSE 0
                    END
                ) AS teams_with_country
            FROM teams
            """
        )

        team_row = cursor.fetchone()

        print()
        print("----------------------------------------")
        print("WORLD MAP DATA STATUS")
        print("----------------------------------------")
        print(
            f"Players with country: "
            f"{player_row[1] or 0}/{player_row[0]}"
        )
        print(
            f"Teams with country  : "
            f"{team_row[1] or 0}/{team_row[0]}"
        )

    finally:
        cursor.close()
        conn.close()



# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":
    enrich_player_profiles(
        limit=50,
        delay_seconds=1.2
    )

    show_country_enrichment_status()