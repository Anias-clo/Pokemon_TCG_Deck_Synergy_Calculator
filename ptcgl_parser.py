import re
from collections import defaultdict

# Create a Global Variable of energy mapping
ENERGY_SYMBOLS = {
    "P": "Psychic",
    "G": "Grass",
    "R": "Fire",
    "W": "Water",
    "L": "Lightning",
    "F": "Fighting",
    "D": "Darkness",
    "M": "Metal",
    "Y": "Fairy",
    "N": "Dragon",
    "C": "Colorless"
}

def parse_decklist(deck_text):
    # Create a defaultDict to extract the card quantity and the
    # supertype: Pokémon, Trainer, Energy
    deck = defaultdict(lambda: {"count": 0, "type": None})

    # Create a variable to store all the cards under a header: Pokémon, Trainer, Energy
    current_section = None

    # Remove whitespace and split the deck into a list
    for line in deck_text.strip().split("\n"):
        line = line.strip()
        # If there isn't any text on a line skip it
        if not line:
            continue

        # Detect section headers
        if line.startswith("Pokémon"):
            current_section = "Pokémon"
            continue
        elif line.startswith("Trainer"):
            current_section = "Trainer"
            continue
        elif line.startswith("Energy"):
            current_section = "Energy"
            continue

        # Match energy lines: 8 Basic {P} Energy Energy 22
        energy_match = re.match(r"(\d+)\s+Basic\s+\{([A-Z])\}\s+Energy", line)
        if energy_match:
            # Extract the two groups
            qty, symbol = energy_match.groups()
            # Use the extracted symbol to pull assign the mapping
            energy_type = ENERGY_SYMBOLS.get(symbol)
            card_name = f"Basic {energy_type} Energy"
            # Assign the number of copies and card supertype to the deck dictionary
            deck[card_name]["count"] += int(qty)
            deck[card_name]["type"] = "Energy"
            continue

        # Match normal card lines: 3 Nest Ball SVI 181 PH
        match = re.match(r"(\d+)\s+(.*?)(?:\s+[A-Z]{2,}\s+\d+.*)?$", line)
        if match:
            # Extract the quantity and name
            qty, card_name = match.groups()
            card_name = card_name.strip()
            # Assign the number of copies and card supertype to the deck dictionary
            deck[card_name]["count"] += int(qty)
            deck[card_name]["type"] = current_section

    return deck