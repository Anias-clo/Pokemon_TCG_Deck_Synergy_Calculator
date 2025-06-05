# Acquire File
import pandas as pd
import numpy as np
import os

DATA_PATH = 'data/cards.csv'

###################### Acquire Pokémon TCG Card Data ########################
def get_card_data():
    '''
    Acquires the Pokémon cards dataset from `cards.csv`.
    Returns a Pandas DataFrame.

    Parameters
    ----------
    None 
    
    Returns
    -------
    df : pandas.core.frame.DataFrame
       Pokémon cards dataset. 
    '''
    global DATA_PATH

    try:
        if os.path.isfile(DATA_PATH):
            return pd.read_csv(DATA_PATH)
    except:
        raise FileNotFoundError("Git gud.")