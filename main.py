from ptcgl_parser import parse_decklist

if __name__ == "__main__":
    # Open the sample Jigglypuff ex Deck
    with open("sample_deck.txt", "r") as f:
        deck_text = f.read()
    # Parse the deck
    parsed = parse_decklist(deck_text)
    for card, count in parsed.items():
        print(f"{card}: {count}")