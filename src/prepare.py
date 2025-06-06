import pandas as pd
import numpy as np
import ast
import re

DATA_PATH = 'data/cards.csv'
stored_data = 'data/pokemon_cleaned.csv'


################################## Prepare Pokémon Cards ######################################
def prep_card_data(dataset):
    '''
    Returns cleaned dataset of Pokémon cards

    Parameters
    ----------
    None 
    
    Returns
    -------
    '''
    dataset = drop_features(dataset)
    dataset = rename_features(dataset)
    dataset = extract_legality(dataset)
    dataset = string_feature_transformation(dataset)
    dataset = pokemon_cards_filter(dataset)
    abilities = get_abilities(dataset)
    attacks = get_attacks(dataset)
    dataset = merge_abilities_and_attacks(abilities,attacks,dataset)
    dataset = stage_and_setup_time(dataset)
    dataset = create_prize_features(dataset)
    dataset = drop_dupes(dataset)
    dataset = arrange_columns(dataset)
    return dataset


def drop_features(dataset):
    '''
    Removes features that are not relevant to synergies
    - Add back resistances and weaknesses at a later date

    Parameters
    ----------
    dataset 
    
    Returns
    -------
    dataset  
    
    '''

    dataset = dataset.drop(columns=['artist', 'ancientTrait', 'cardmarket',
                                    'flavorText', 'images', 'nationalPokedexNumbers',
                                    'rarity', 'retreatCost', 'tcgplayer', 'resistances',
                                    'weaknesses']).reset_index(drop=True)
    
    return dataset


def rename_features(dataset):
    '''
    Lowercase and rename columns

    Parameters
    ----------
    dataset 
    
    Returns
    -------
    dataset
    '''
    dataset.columns = [column.lower() for column in dataset.columns]

    # Rename columns with more descriptive names
    dataset.rename(columns={'evolvesfrom':'evolves_from',
                            'convertedretreatcost':'retreat_cost',
                            'regulationmark':'regulation_mark',},
                   inplace=True)


    return dataset

def extract_legality(dataset):
    '''
    Rearranges columns

    Parameters
    ----------
    dataset 
    
    Returns
    -------
    dataset
    '''
    # Extract the standard format legality flag
    dataset['standard_legality'] = dataset['legalities']\
                                        .apply(ast.literal_eval)\
                                        .apply(lambda d: d.get('standard'))

    return dataset


def string_feature_transformation(dataset):
    '''
    This function casts nested columns into strings
    '''
    # Transform the columns into a strings
    dataset['subtypes'] = dataset['subtypes'].apply(
                                    lambda x: str(sorted(ast.literal_eval(x))) if pd.notnull(x) else [])
    
    columns_to_cast = ['abilities', 'attacks', 'set', 'rules']
    
    for col in columns_to_cast:
        dataset[col] = dataset[col].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else x)

    return dataset


def pokemon_cards_filter(dataset):
    '''
    This function accepts the standard legal pokemon cards and filters for cards
    with a supertype of pok´mon only.
    '''
    # Filter the dataset for only Pokémon cards
    dataset = dataset[(dataset['standard_legality']=='Legal')&\
                        (dataset['regulation_mark']>='G')&
                        (dataset['supertype']=='Pokémon')].reset_index(drop=True)

    return dataset


def get_abilities(dataset):
    '''
    
    '''
    # Drop rows with missing abilities
    df_abilities = dataset.dropna(subset=['abilities']).copy()

    # Flatten the abilities list
    df_abilities = df_abilities.explode('abilities')
    df_abilities['ability_name'] = df_abilities['abilities'].apply(lambda x: x.get('name') if isinstance(x, dict) else None)
    df_abilities['ability_text'] = df_abilities['abilities'].apply(lambda x: x.get('text') if isinstance(x, dict) else None)
    df_abilities['ability_type'] = df_abilities['abilities'].apply(lambda x: x.get('type') if isinstance(x, dict) else None)

    df_abilities = df_abilities[['id', 'ability_name', 'ability_text']].reset_index(drop=True)
    df_abilities.to_csv('data/pokemon_abilities.csv', index=False)

    return df_abilities


def get_attacks(dataset):
    '''
    
    '''
    # Drop rows with missing attacks
    df_attacks = dataset.dropna(subset=['attacks']).copy()
    
    # Flatten the attacks list
    df_attacks = df_attacks.explode('attacks')
    df_attacks['attack_name'] = df_attacks['attacks'].apply(lambda x: x.get('name') if isinstance(x, dict) else None)
    df_attacks['attack_text'] = df_attacks['attacks'].apply(lambda x: x.get('text') if isinstance(x, dict) else None)
    df_attacks['attack_damage'] = df_attacks['attacks'].apply(lambda x: x.get('damage') if isinstance(x, dict) else None)
    df_attacks['attack_cost'] = df_attacks['attacks'].apply(lambda x: x.get('cost') if isinstance(x, dict) else None)
    df_attacks['attack_energy_cost'] = df_attacks['attacks'].apply(lambda x: x.get('convertedEnergyCost') if isinstance(x, dict) else None)

    df_attacks = df_attacks[['id', 'attack_name', 'attack_text', 'attack_damage', 'attack_cost', 'attack_energy_cost']].reset_index(drop=True)
    df_attacks.to_csv('data/pokemon_attacks.csv', index=False)

    return df_attacks


def merge_abilities_and_attacks(abilities,attacks,dataset):
    '''
    This function merges the abilities and attacks dataframe back to the pokémon cards
    '''
    dataset = dataset.merge(abilities, how='left', on='id')
    dataset = dataset.merge(attacks, how='left', on='id')
    return dataset


# Create a function to extract the stage and the number of cards need to reach that stage
def extract_stage(subtypes):
    '''Extract the Stage of each Pokémon card'''
    if not isinstance(subtypes, str):
        return (None, None)
    if 'Basic' in subtypes:
        return ('Basic', 0)
    elif 'Stage 1' in subtypes:
        return ('Stage 1', 1)
    elif 'Stage 2' in subtypes:
        return ('Stage 2', 2)
    return (None, None)


# Apply the function to your DataFrame
def stage_and_setup_time(dataset):
    '''
    This function extracts the stage of a pokémon and the number of turns it takes to get a card on the field.
    '''
    dataset[['stage', 'setup_time']] = dataset['subtypes'].apply(extract_stage).apply(pd.Series)
    
    return dataset


def extract_prize_value(rule):
    # Handle missing or empty rule values
    if rule is None or rule == '' or rule == []:
        return 1
    
    # If the rule is a stringified list, convert it to an actual list
    if isinstance(rule, str):
        try:
            rule = ast.literal_eval(rule)
        except Exception:
            return 1

    # At this point, rule should be a list
    if isinstance(rule, list):
        for r in rule:
            match = re.search(r'takes (\d+) Prize', r)
            if match:
                return int(match.group(1))

    return 1


def create_prize_features(dataset):
    '''
    
    '''
    dataset['primary_type'] = dataset['types'].apply(
    lambda x: ast.literal_eval(x)[0] if pd.notnull(x) else x)
    dataset['is_ex'] = dataset['subtypes'].apply(lambda x: 1 if 'ex' in x else 0)
    dataset['is_tera'] = dataset['subtypes'].apply(lambda x: 1 if 'Tera' in x else 0)
    dataset['prize_card_value'] = dataset['rules'].apply(extract_prize_value)
    # dataset['release_date'] = dataset['set'].apply(lambda x: x.get('releaseDate') if isinstance(x, dict) else None)
    # dataset['release_date'] = pd.to_datetime(dataset['release_date'], errors='coerce')
    # dataset['release_year'] = dataset['release_date'].dt.year
    # Create the feature flag for bench damage immunity
    dataset['set_name'] = dataset['set'].apply(lambda x: x.get('id') if isinstance(x,dict) else None)
    dataset.rename(columns={'number': 'set_number'},inplace=True)
    dataset['set_number'] = dataset['set_number'].astype('int')
    dataset['is_immune_to_bench_damage'] = dataset['rules'].apply(
        lambda x: int(any('As long as this Pokémon is on your Bench, prevent all damage done' in rule for rule in x)) if isinstance(x, list) else 0
        )
    dataset['attack_damage_amount'] = dataset['attack_damage'].str.extract('([0-9]*)')
    dataset['attack_damage_modifier'] = dataset['attack_damage'].str.extract('([+-×])')
    dataset['cards_needed_for_attack'] = dataset['setup_time'] + dataset['attack_energy_cost']
    dataset['attack_damage_amount'] = pd.to_numeric(dataset['attack_damage_amount'], errors='coerce')
    dataset['is_coin_flip'] = dataset['attack_text'].str.contains('coin')
    dataset['damage_per_energy'] = np.where(dataset['attack_energy_cost'] == 0,
                                                     np.nan,  # or 0 if you prefer
                                                     round(dataset['attack_damage_amount'] / dataset['attack_energy_cost'], 2)
                                                     )

    dataset['damage_per_energy'] = pd.to_numeric(dataset['damage_per_energy'], errors='coerce')

    return dataset


def drop_dupes(dataset):
    '''
    Removes duplicate cards from the dataset.

    Parameters
    ----------
    dataset 
    
    Returns
    -------
    dataset
    
    '''
    # Remove rarity duplicates
    dataset = dataset.drop_duplicates(subset=['name', 'attack_name', 'hp', 'ability_name'],keep='first'
                                     ).reset_index(drop=True)

    return dataset


def arrange_columns(dataset):
    '''
    Rearranges columns

    Parameters
    ----------
    dataset 
    
    Returns
    -------
    dataset
    '''
    dataset = dataset[['id',
    'set_name',
    'set_number',
    'supertype',
    'name',
    'stage',
    'is_ex',
    'is_tera',
    'primary_type',
    'evolves_from',
    'hp',
    'ability_name',
    'ability_text',
    'attack_name',
    'attack_text',
    'attack_damage_amount',
    'attack_damage_modifier',
    'attack_cost',
    'cards_needed_for_attack',
    'attack_energy_cost',
    'is_coin_flip',
    'damage_per_energy',
    'retreat_cost',
    'prize_card_value',
    'setup_time',
    'is_immune_to_bench_damage'
    ]].sort_values(by=['set_name','set_number']).reset_index(drop=True)

    return dataset