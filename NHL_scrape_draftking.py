import requests
from bs4 import BeautifulSoup
from collections import defaultdict

def get_draftkings_data():
    """
    Fetch NHL betting odds from DraftKings and standardize the data structure.
    
    Returns:
        A list of dictionaries, where each dictionary contains betting data for one game:
            - team1: Name of the first team.
            - team2: Name of the second team.
            - spread_team1: Puckline odds for team1.
            - spread_team2: Puckline odds for team2.
            - total_team1: Total odds for team1.
            - total_team2: Total odds for team2.
            - moneyline_team1: Moneyline odds for team1.
            - moneyline_team2: Moneyline odds for team2.
    """
    url = "https://sportsbook.draftkings.com/leagues/hockey/nhl"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failed to fetch page, status code:", response.status_code)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    # Use a defaultdict to group rows by event (game)
    events = defaultdict(list)

    # Each row corresponds to a team's betting info.
    for row in soup.find_all("tr"):
        # Extract the link element which contains event info
        link = row.find("a", class_="event-cell-link")
        if not link:
            continue

        # Get the event id from the link URL (using the last segment)
        href = link.get("href")
        event_id = href.split("/")[-1]

        # Extract the team name
        team_div = row.find("div", class_="event-cell__name-text")
        team_name = team_div.text.strip() if team_div else "N/A"

        # We expect three td cells: [puckline, total, moneyline]
        tds = row.find_all("td", class_="sportsbook-table__column-row")
        if len(tds) < 3:
            continue

        # Get puckline (used as spread), total, and moneyline odds
        puckline_span = tds[0].find("span", class_="sportsbook-odds")
        puckline = puckline_span.text.strip() if puckline_span else "N/A"

        total_span = tds[1].find("span", class_="sportsbook-odds")
        total = total_span.text.strip() if total_span else "N/A"

        moneyline_span = tds[2].find("span", class_="sportsbook-odds")
        moneyline = moneyline_span.text.strip() if moneyline_span else "N/A"

        team_data = {
            "team": team_name,
            "puckline": puckline,
            "total": total,
            "moneyline": moneyline
        }
        events[event_id].append(team_data)

    # Standardize the output so that each game is represented as one dictionary
    games_list = []
    for event_id, teams in events.items():
        if len(teams) >= 2:
            game_data = {
                "team1": teams[0]["team"],
                "team2": teams[1]["team"],
                "spread_team1": teams[0]["puckline"],
                "spread_team2": teams[1]["puckline"],
                "total_team1": teams[0]["total"],
                "total_team2": teams[1]["total"],
                "moneyline_team1": teams[0]["moneyline"],
                "moneyline_team2": teams[1]["moneyline"]
            }
            games_list.append(game_data)

    return games_list

# For testing the function when running this module directly
if __name__ == "__main__":
    data = get_draftkings_data()
    for game in data:
        print(f"{game['team1']} vs {game['team2']}:")
        print(f"  Spread: {game['spread_team1']} | {game['spread_team2']}")
        print(f"  Total: {game['total_team1']} | {game['total_team2']}")
        print(f"  Moneyline: {game['moneyline_team1']} | {game['moneyline_team2']}")
        print("-" * 50)
