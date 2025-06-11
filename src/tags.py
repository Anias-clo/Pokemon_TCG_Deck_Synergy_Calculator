import pandas as pd
import re

def tag_trainer_mechanics(df):
    """Add 'mechanic_tags' column based on card name and rules text."""
    keyword_map = {
        "search": ["search your deck", "look for", "reveal a card"],
        "draw": ["draw", "cards from your deck"],
        "switch": ["switch", "swap"],
        "evolve": ["evolve", "evolution"],
        "heal": ["heal", "remove damage"],
        "discard": ["discard", "put in the discard pile"],
        "energy_accel": ["attach", "energy", "basic energy", "accelerate"],
    }
    
    def tag_rules(rules_text):
        tags = set()
        if isinstance(rules_text, str):
            lowered = rules_text.lower()
            for tag, keywords in keyword_map.items():
                if any(k in lowered for k in keywords):
                    tags.add(tag)
        return list(tags)
    
    df['mechanic_tags'] = df['rules'].apply(tag_rules)
    return df

def tag_energy_types(df):
    """Add 'energy_type_tags' column based on card name."""
    energy_keywords = ['Grass', 'Fire', 'Water', 'Lightning', 'Psychic', 'Fighting', 
                       'Darkness', 'Metal', 'Fairy', 'Dragon', 'Colorless']

    def tag_from_name(name):
        tags = []
        for ek in energy_keywords:
            if ek.lower() in name.lower():
                tags.append(ek)
        return tags

    df['energy_type_tags'] = df['name'].apply(tag_from_name)
    return df