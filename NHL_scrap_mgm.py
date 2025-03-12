import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def get_betting_data():
    """
    Fetch NHL betting data from BetMGM using Selenium and BeautifulSoup.
    
    Returns:
        A list of dictionaries, each containing betting data for a game.
        Each dictionary includes:
            - team1: Name of the first team.
            - team2: Name of the second team.
            - spread_team1: Spread odds for team1.
            - spread_team2: Spread odds for team2.
            - total_team1: Total odds for team1.
            - total_team2: Total odds for team2.
            - moneyline_team1: Moneyline odds for team1.
            - moneyline_team2: Moneyline odds for team2.
    """
    # Set up Selenium with headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)

    url = "https://sports.on.betmgm.ca/en/sports/hockey-12/betting/usa-9/nhl-34"
    driver.get(url)

    # Wait until at least one game block is loaded
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "ms-six-pack-event"))
        )
    except Exception as e:
        print("Timed out waiting for game elements to load:", e)
        driver.quit()
        return []

    # Allow extra time for all JS to render
    time.sleep(2)
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    game_blocks = soup.find_all("ms-six-pack-event")
    if not game_blocks:
        return []

    def safe_text(element):
        return element.get_text(strip=True) if element else "N/A"

    games_data = []

    for game in game_blocks:
        # Extract team names from event name block
        event_name_block = game.find("ms-event-name", class_="grid-event-name")
        if event_name_block:
            team_elements = event_name_block.find_all("div", class_="participant ng-star-inserted")
            if len(team_elements) >= 2:
                team1 = safe_text(team_elements[0])
                team2 = safe_text(team_elements[1])
            else:
                team1 = team2 = "N/A"
        else:
            team1 = team2 = "N/A"

        # Expecting three odds groups: spread, total, moneyline
        option_groups = game.find_all("ms-option-group")
        if len(option_groups) < 3:
            continue  # Skip incomplete entries

        # Spread odds (first group)
        spread_options = option_groups[0].find_all("ms-option")
        if len(spread_options) >= 2:
            spread_team1 = safe_text(spread_options[0].find("span", class_="custom-odds-value-style"))
            spread_team2 = safe_text(spread_options[1].find("span", class_="custom-odds-value-style"))
        else:
            spread_team1 = spread_team2 = "N/A"

        # Total odds (second group)
        total_options = option_groups[1].find_all("ms-option")
        if len(total_options) >= 2:
            total_team1 = safe_text(total_options[0].find("span", class_="custom-odds-value-style"))
            total_team2 = safe_text(total_options[1].find("span", class_="custom-odds-value-style"))
        else:
            total_team1 = total_team2 = "N/A"

        # Moneyline odds (third group)
        moneyline_options = option_groups[2].find_all("ms-option")
        if len(moneyline_options) >= 2:
            moneyline_team1 = safe_text(moneyline_options[0].find("span", class_="custom-odds-value-style"))
            moneyline_team2 = safe_text(moneyline_options[1].find("span", class_="custom-odds-value-style"))
        else:
            moneyline_team1 = moneyline_team2 = "N/A"

        game_data = {
            "team1": team1,
            "team2": team2,
            "spread_team1": spread_team1,
            "spread_team2": spread_team2,
            "total_team1": total_team1,
            "total_team2": total_team2,
            "moneyline_team1": moneyline_team1,
            "moneyline_team2": moneyline_team2,
        }
        games_data.append(game_data)

    return games_data

# For debugging or standalone run
if __name__ == "__main__":
    data = get_betting_data()
    for game in data:
        print(game)
