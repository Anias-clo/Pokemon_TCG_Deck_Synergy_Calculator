# Refactor the contents to organize the trainer processing into a function with docstrings and clean structure

import pandas as pd
import ast

def extract_subtype(subtype):
    '''Extract the first subtype from a list of subtypes.'''
    if not isinstance(subtype, list):
        return None
    return subtype[0]

def prep_energy_df(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Clean and process Trainer card data from the Pokémon TCG dataset.
    
    Args:
        df (pd.DataFrame): Raw Pokémon card dataset including all supertypes.
        
    Returns:
        pd.DataFrame: Cleaned Trainer cards dataframe with subtype extraction.
    '''
    df = df.copy()
    df = df[df['supertype'] == 'Energy']

    # Clean up name field
    df['name'] = df['name'].str.replace(r'\\s*\\(.*?\\)', '', regex=True).str.strip()

    # Sort by name and subtype for deduplication
    df = df.sort_values(by=['name', 'subtypes'], ascending=False)

    # Parse nested features
    for col in ['abilities', 'attacks', 'set', 'rules']:
        df[col] = df[col].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else x)

    df['set_name'] = df['set'].apply(lambda x: x.get('id') if isinstance(x, dict) else None)
    df.rename(columns={'number': 'set_number'}, inplace=True)

    # Filter by legality (Regulation Mark G or later)
    df = df[df['regulationMark'] >= 'G'].reset_index(drop=True)

    # Add an ACE SPEC feature
    df['is_ace_spec'] = df['subtypes'].apply(lambda x: 1 if 'ACE SPEC' in x else 0)

    # Drop duplicates by name
    # df = df.drop_duplicates(subset=['name'], keep='first').reset_index(drop=True)

    # Parse subtypes from string to list
    df['subtypes'] = df['subtypes'].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else None)

    # Extract first subtype
    df['subtype'] = df['subtypes'].apply(extract_subtype)

    # Drop unnecessary columns if they exist
    drop_cols = ['artist', 'ancientTrait', 'cardmarket', 'flavorText',
                 'images', 'nationalPokedexNumbers', 'rarity',
                 'retreatCost','tcgplayer', 'resistances', 'weaknesses']
    
    df.drop(columns=drop_cols, inplace=True, errors='ignore')

    # Rearrange columns
    df = df[['id',
             'supertype',
             'subtype',
             'name',
             'is_ace_spec',
             'rules',
             'set_number',
             'set_name'
             ]]

    return df