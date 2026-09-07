from database.connection import get_connection


def create_player(
    player_id,
    player_name,
    role=None,
    batting_style=None,
    bowling_style=None,
    country=None,
    team_id=None
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        INSERT INTO players (
            player_id,
            player_name,
            role,
            batting_style,
            bowling_style,
            country,
            team_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(
            query,
            player_id,
            player_name,
            role,
            batting_style,
            bowling_style,
            country,
            team_id
        )

        conn.commit()
        print("Player created successfully ✅")

    except Exception as error:
        conn.rollback()
        print("Create failed ❌")
        print(error)

    finally:
        cursor.close()
        conn.close()


def read_players():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        SELECT TOP 50
            player_id,
            player_name,
            role,
            batting_style,
            bowling_style,
            country,
            team_id
        FROM players
        ORDER BY player_name
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        return rows

    finally:
        cursor.close()
        conn.close()


def update_player(
    player_id,
    player_name,
    role=None,
    batting_style=None,
    bowling_style=None,
    country=None
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        UPDATE players
        SET
            player_name = ?,
            role = ?,
            batting_style = ?,
            bowling_style = ?,
            country = ?,
            updated_at = GETDATE()
        WHERE player_id = ?
        """

        cursor.execute(
            query,
            player_name,
            role,
            batting_style,
            bowling_style,
            country,
            player_id
        )

        conn.commit()
        print("Player updated successfully ✅")

    except Exception as error:
        conn.rollback()
        print("Update failed ❌")
        print(error)

    finally:
        cursor.close()
        conn.close()


def delete_player(player_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        DELETE FROM players
        WHERE player_id = ?
        """

        cursor.execute(
            query,
            player_id
        )

        conn.commit()
        print("Player deleted successfully ✅")

    except Exception as error:
        conn.rollback()
        print("Delete failed ❌")
        print(error)

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("CRUD Module Ready ✅")