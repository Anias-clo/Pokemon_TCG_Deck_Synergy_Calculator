import pandas as pd
import numpy as np
import ast
import re
import os

DATA_PATH = 'data/cards.csv'
STORED_DATA = 'data/pokemon_cleaned.csv'

def prep_pokemon_data(dataset):
    """
    Clean and process a raw Pokémon card dataset to prepare it for synergy analysis.
    """
    global STORED_DATA

    if os.path.exists(STORED_DATA):
        return pd.read_csv(STORED_DATA)

    dataset = drop_features(dataset)
    dataset = rename_features(dataset)
    dataset = extract_legality(dataset)
    dataset = string_feature_transformation(dataset)
    dataset = pokemon_cards_filter(dataset)
    abilities = get_abilities(dataset)
    attacks = get_attacks(dataset)
    dataset = merge_abilities_and_attacks(abilities, attacks, dataset)
    dataset = stage_and_setup_time(dataset)
    dataset = create_prize_features(dataset)
    dataset = drop_dupes(dataset)
    dataset = arrange_columns(dataset)
    dataset.to_csv(STORED_DATA, index=False)
    return dataset

def drop_features(dataset):
    drop_cols = [
        'artist', 'ancientTrait', 'cardmarket', 'flavorText', 'images',
        'nationalPokedexNumbers', 'rarity', 'retreatCost', 'tcgplayer',
        'resistances', 'weaknesses'
    ]
    return dataset.drop(columns=drop_cols).reset_index(drop=True)

def rename_features(dataset):
    dataset.columns = [col.lower() for col in dataset.columns]
    return dataset.rename(columns={
        'evolvesfrom': 'evolves_from',
        'convertedretreatcost': 'retreat_cost',
        'regulationmark': 'regulation_mark'
    })

def extract_legality(dataset):
    dataset['standard_legality'] = dataset['legalities'].apply(ast.literal_eval).apply(lambda d: d.get('standard'))
    return dataset

def string_feature_transformation(dataset):
    dataset['subtypes'] = dataset['subtypes'].apply(lambda x: str(sorted(ast.literal_eval(x))) if pd.notnull(x) else [])
    for col in ['abilities', 'attacks', 'set', 'rules']:
        dataset[col] = dataset[col].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else x)
    return dataset

def pokemon_cards_filter(dataset):
    return dataset[(dataset['standard_legality'] == 'Legal') &
                   (dataset['regulation_mark'] >= 'G') &
                   (dataset['supertype'] == 'Pokémon')].reset_index(drop=True)

def get_abilities(dataset):
    df = dataset.dropna(subset=['abilities']).copy().explode('abilities')
    df['ability_name'] = df['abilities'].apply(lambda x: x.get('name') if isinstance(x, dict) else None)
    df['ability_text'] = df['abilities'].apply(lambda x: x.get('text') if isinstance(x, dict) else None)
    df['ability_type'] = df['abilities'].apply(lambda x: x.get('type') if isinstance(x, dict) else None)
    df = df[['id', 'ability_name', 'ability_text']].reset_index(drop=True)
    df.to_csv('data/pokemon_abilities.csv', index=False)
    return df

def get_attacks(dataset):
    df = dataset.dropna(subset=['attacks']).copy().explode('attacks')
    df['attack_name'] = df['attacks'].apply(lambda x: x.get('name') if isinstance(x, dict) else None)
    df['attack_text'] = df['attacks'].apply(lambda x: x.get('text') if isinstance(x, dict) else None)
    df['attack_damage'] = df['attacks'].apply(lambda x: x.get('damage') if isinstance(x, dict) else None)
    df['attack_cost'] = df['attacks'].apply(lambda x: x.get('cost') if isinstance(x, dict) else None)
    df['attack_energy_cost'] = df['attacks'].apply(lambda x: x.get('convertedEnergyCost') if isinstance(x, dict) else None)
    df = df[['id', 'attack_name', 'attack_text', 'attack_damage', 'attack_cost', 'attack_energy_cost']].reset_index(drop=True)
    df.to_csv('data/pokemon_attacks.csv', index=False)
    return df

def merge_abilities_and_attacks(abilities, attacks, dataset):
    return dataset.merge(abilities, how='left', on='id').merge(attacks, how='left', on='id')

def extract_stage(subtypes):
    if not isinstance(subtypes, str):
        return (None, None)
    if 'Basic' in subtypes:
        return ('Basic', 0)
    if 'Stage 1' in subtypes:
        return ('Stage 1', 1)
    if 'Stage 2' in subtypes:
        return ('Stage 2', 2)
    return (None, None)

def stage_and_setup_time(dataset):
    dataset[['stage', 'setup_time']] = dataset['subtypes'].apply(extract_stage).apply(pd.Series)
    return dataset

def extract_prize_value(rule):
    if rule is None or rule in ('', []):
        return 1
    if isinstance(rule, str):
        try:
            rule = ast.literal_eval(rule)
        except Exception:
            return 1
    if isinstance(rule, list):
        for r in rule:
            match = re.search(r'takes (\d+) Prize', r)
            if match:
                return int(match.group(1))
    return 1

def create_prize_features(dataset):
    dataset['primary_type'] = dataset['types'].apply(lambda x: ast.literal_eval(x)[0] if pd.notnull(x) else x)
    dataset['is_future'] = dataset['subtypes'].apply(lambda x: 1 if 'Future' in x else 0)
    dataset['is_ancient'] = dataset['subtypes'].apply(lambda x: 1 if 'Ancient' in x else 0)
    dataset['is_ex'] = dataset['subtypes'].apply(lambda x: 1 if 'ex' in x else 0)
    dataset['is_tera'] = dataset['subtypes'].apply(lambda x: 1 if 'Tera' in x else 0)
    dataset['prize_card_value'] = dataset['rules'].apply(extract_prize_value)
    dataset['set_name'] = dataset['set'].apply(lambda x: x.get('id') if isinstance(x, dict) else None)
    dataset.rename(columns={'number': 'set_number'}, inplace=True)
    dataset['set_number'] = dataset['set_number'].astype(int)
    dataset['is_immune_to_bench_damage'] = dataset['rules'].apply(
        lambda x: int(any('As long as this Pokémon is on your Bench, prevent all damage done' in rule for rule in x)) if isinstance(x, list) else 0
    )
    dataset['attack_damage_amount'] = pd.to_numeric(dataset['attack_damage'].str.extract(r'(\d*)')[0], errors='coerce')
    dataset['attack_damage_modifier'] = dataset['attack_damage'].str.extract(r'([+-×])')[0]
    dataset['cards_needed_for_attack'] = dataset['setup_time'] + dataset['attack_energy_cost']
    dataset['is_coin_flip'] = dataset['attack_text'].str.contains('coin')
    dataset['damage_per_energy'] = np.where(dataset['attack_energy_cost'] == 0, np.nan,
                                            round(dataset['attack_damage_amount'] / dataset['attack_energy_cost'], 2))
    dataset['damage_per_energy'] = pd.to_numeric(dataset['damage_per_energy'], errors='coerce')
    return dataset

def drop_dupes(dataset):
    return dataset.drop_duplicates(subset=['name', 'attack_name', 'hp', 'ability_name'], keep='first').reset_index(drop=True)

def arrange_columns(dataset):
    columns = [
        'id', 'set_name', 'set_number', 'supertype', 'name', 'stage', 'is_future',
        'is_ancient','is_ex', 'is_tera', 'primary_type', 'evolves_from', 'hp', 'ability_name',
        'ability_text', 'attack_name', 'attack_text', 'attack_damage_amount', 'attack_damage_modifier',
        'attack_cost', 'cards_needed_for_attack', 'attack_energy_cost', 'is_coin_flip',
        'damage_per_energy', 'retreat_cost', 'prize_card_value', 'setup_time', 'is_immune_to_bench_damage'
    ]
    return dataset[columns].sort_values(by=['set_name', 'set_number']).reset_index(drop=True)
