import requests

from config import BASE_URL, RAPIDAPI_HOST, RAPIDAPI_KEY


class CrickbuzzClient:
    """Handles requests to the Crickbuzz API."""

    def __init__(self):
        self.headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json",
        }

    def get_home_data(self):
        url = f"{BASE_URL}/home"
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return response.json()

    def get_live_matches(self):
        url = f"{BASE_URL}/matches/live"
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return response.json()

    def get_upcoming_matches(self):
        url = f"{BASE_URL}/matches/upcoming"
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return response.json()

    def get_recent_matches(self):
        url = f"{BASE_URL}/matches/recent"
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return response.json()

    def get_player_details(self, player_id):
        url = f"{BASE_URL}/browse/player/{player_id}"
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return response.json()

    def get_team_players(self, team_id):
        url = f"{BASE_URL}/team/{team_id}/players"
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return response.json()

    def get_series_info(self, series_id):
        url = f"{BASE_URL}/series/{series_id}"
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return response.json()

    def get_venue_details(self, venue_id):
        url = f"{BASE_URL}/venue/{venue_id}"
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return response.json()

    def get_match_scorecard(self, match_id):
        url = f"{BASE_URL}/match/{match_id}/scorecard"

        params = {
            "matchID": str(match_id)
        }

        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            timeout=20
        )

        response.raise_for_status()
        return response.json()