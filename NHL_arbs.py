import re
import time
import threading
import tkinter as tk
from tkinter import ttk

# Import the two functions from the modules
from NHL_scrap_mgm import get_betting_data  # BetMGM data
from NHL_scrape_draftking import get_draftkings_data  # DraftKings data

# ----------------------------
# Helper Functions
# ----------------------------

def convert_to_decimal(odds):
    """Converts odds to decimal format."""
    if odds == "N/A":
        return None
        
    odds_str = str(odds).strip().replace("−", "-")
    # Check for American odds format
    if odds_str.startswith('+'):
        return float(odds_str[1:]) / 100 + 1
    elif odds_str.startswith('-'):
        return 100 / float(odds_str[1:]) + 1
    else:
        try:
            # Assume it's already a decimal value
            return float(odds_str)
        except (ValueError, TypeError):
            return None

def standardize_team_name(team_name):
    """Standardizes team names."""
    team_name = team_name.strip()
    parts = team_name.split()
    if len(parts) > 1 and parts[0].isupper() and len(parts[0]) == 3:
        team_name = " ".join(parts[1:])
    return team_name.lower()

def normalized_team(team_name):
    """Normalizes a team name."""
    std_name = standardize_team_name(team_name)
    return re.sub(r'\W+', '', std_name)

def normalized_game_key(game):
    """Returns a sorted tuple of normalized team names."""
    team1 = normalized_team(game.get('team1', ''))
    team2 = normalized_team(game.get('team2', ''))
    return tuple(sorted([team1, team2]))

def calculate_arbitrage(total_stake, odds_a, odds_b):
    """Calculates arbitrage opportunity details."""
    if odds_a is None or odds_b is None:
        return None
        
    reciprocal_a = 1 / odds_a
    reciprocal_b = 1 / odds_b
    arb_percentage = reciprocal_a + reciprocal_b
    
    # Only proceed if there's an arbitrage opportunity
    if arb_percentage >= 1:
        return None
    
    stake_a = total_stake * reciprocal_a / arb_percentage
    stake_b = total_stake * reciprocal_b / arb_percentage
    payout = stake_a * odds_a  # Should equal stake_b * odds_b
    profit = payout - total_stake
    profit_pct = (profit / total_stake) * 100
    
    return {
        'arb_percentage': arb_percentage,
        'stake_a': stake_a,
        'stake_b': stake_b,
        'payout': payout,
        'profit': profit,
        'profit_pct': profit_pct
    }

def find_arbitrage_opportunities(total_stake=100):
    # Retrieve betting data from both sources
    print("Retrieving betting data from BetMGM...")
    mgm_data = get_betting_data()
    print("Retrieving betting data from DraftKings...")
    dk_data = get_draftkings_data()
    print(f"Found {len(mgm_data)} games on BetMGM and {len(dk_data)} games on DraftKings")
    
    # Build a dictionary of DraftKings games keyed by normalized team names
    dk_games = {}
    for game in dk_data:
        key = normalized_game_key(game)
        dk_games[key] = game

    arbitrage_list = []
    matched_games = 0

    # For each BetMGM game, try to find a matching DraftKings game
    for mgm_game in mgm_data:
        key = normalized_game_key(mgm_game)
        if key in dk_games:
            matched_games += 1
            dk_game = dk_games[key]
            team1, team2 = key[0].capitalize(), key[1].capitalize()
            
            # Check for arbitrage in all three bet types
            bet_types = [
                ('Moneyline', 'moneyline_team1', 'moneyline_team2'),
                ('Spread', 'spread_team1', 'spread_team2'),
                ('Total', 'total_team1', 'total_team2')
            ]
            
            for bet_type, field1, field2 in bet_types:
                try:
                    # Convert odds to decimal and find the best for each team
                    mgm_odds1 = convert_to_decimal(mgm_game[field1])
                    dk_odds1 = convert_to_decimal(dk_game[field1])
                    
                    mgm_odds2 = convert_to_decimal(mgm_game[field2])
                    dk_odds2 = convert_to_decimal(dk_game[field2])
                    
                    # Skip if any odds are missing
                    if None in [mgm_odds1, dk_odds1, mgm_odds2, dk_odds2]:
                        continue
                    
                    best_odds1 = max(mgm_odds1, dk_odds1)
                    best_odds1_source = "BetMGM" if best_odds1 == mgm_odds1 else "DraftKings"
                    
                    best_odds2 = max(mgm_odds2, dk_odds2)
                    best_odds2_source = "BetMGM" if best_odds2 == mgm_odds2 else "DraftKings"
                    
                    # For totals, we're typically betting Over/Under rather than teams
                    display_team1 = "Over" if bet_type == "Total" else team1
                    display_team2 = "Under" if bet_type == "Total" else team2
                    
                    arb_result = calculate_arbitrage(total_stake, best_odds1, best_odds2)
                    if arb_result:
                        arbitrage_info = {
                            'teams': key,
                            'display_team1': display_team1,
                            'display_team2': display_team2,
                            'odds1': best_odds1,
                            'odds1_source': best_odds1_source,
                            'odds2': best_odds2,
                            'odds2_source': best_odds2_source,
                            'arb_result': arb_result,
                            'bet_type': bet_type
                        }
                        arbitrage_list.append(arbitrage_info)
                
                except Exception:
                    continue
    
    print(f"Successfully matched {matched_games} games between BetMGM and DraftKings")
    return arbitrage_list

# ----------------------------
# Tkinter GUI Application
# ----------------------------

class ArbitrageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NHL Arbitrage Opportunities")
        self.geometry("1200x600")

        # Create a Treeview with appropriate columns
        self.tree = ttk.Treeview(self, columns=("Game", "Bet Type", "Team1", "Team2", "Arb %", "Stake1", "Stake2", "Profit", "Profit %"), show="headings")
        self.tree.heading("Game", text="Game")
        self.tree.heading("Bet Type", text="Bet Type")
        self.tree.heading("Team1", text="Team1 (Odds, Source)")
        self.tree.heading("Team2", text="Team2 (Odds, Source)")
        self.tree.heading("Arb %", text="Arb %")
        self.tree.heading("Stake1", text="Stake1")
        self.tree.heading("Stake2", text="Stake2")
        self.tree.heading("Profit", text="Profit")
        self.tree.heading("Profit %", text="Profit %")
        self.tree.column("Game", width=200)
        self.tree.column("Bet Type", width=100)
        self.tree.column("Team1", width=200)
        self.tree.column("Team2", width=200)
        self.tree.column("Arb %", width=80)
        self.tree.column("Stake1", width=80)
        self.tree.column("Stake2", width=80)
        self.tree.column("Profit", width=80)
        self.tree.column("Profit %", width=80)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Dictionary to keep track of displayed bets: key -> tree item id
        self.displayed_bets = {}

        # Start the arbitrage scanning process
        self.start_scan()

    def get_bet_key(self, bet):
        # Unique key composed of game and bet type
        return f"{bet['teams'][0].capitalize()} vs {bet['teams'][1].capitalize()} - {bet['bet_type']}"

    def update_display(self, new_bets):
        # Create a set of keys for the new arbitrage opportunities
        new_keys = set()
        for bet in new_bets:
            key = self.get_bet_key(bet)
            new_keys.add(key)
            if key not in self.displayed_bets:
                values = (
                    f"{bet['teams'][0].capitalize()} vs {bet['teams'][1].capitalize()}",
                    bet['bet_type'],
                    f"{bet['display_team1']}: {bet['odds1']:.2f} ({bet['odds1_source']})",
                    f"{bet['display_team2']}: {bet['odds2']:.2f} ({bet['odds2_source']})",
                    f"{bet['arb_result']['arb_percentage']*100:.2f}%",
                    f"${bet['arb_result']['stake_a']:.2f}",
                    f"${bet['arb_result']['stake_b']:.2f}",
                    f"${bet['arb_result']['profit']:.2f}",
                    f"{bet['arb_result']['profit_pct']:.2f}%"
                )
                item_id = self.tree.insert("", "end", values=values)
                self.displayed_bets[key] = item_id

        # Remove any bets that are no longer found
        for key in list(self.displayed_bets.keys()):
            if key not in new_keys:
                self.tree.delete(self.displayed_bets[key])
                del self.displayed_bets[key]

    def scan_arbitrage(self):
        # Run the arbitrage scan (this might take a few seconds due to web calls)
        new_bets = find_arbitrage_opportunities(total_stake=100)
        # Schedule the update on the main thread
        self.after(0, self.update_display, new_bets)
        # Schedule the next scan in 15 seconds
        self.after(15000, self.start_scan)

    def start_scan(self):
        # Use a thread to avoid blocking the GUI while scanning
        threading.Thread(target=self.scan_arbitrage, daemon=True).start()

if __name__ == "__main__":
    app = ArbitrageApp()
    app.mainloop()
