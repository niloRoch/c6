import pandas as pd
import numpy as np

def calculate_leverage_suggestion(df):
    """
    Calcula sugestão de alavancagem baseada no score de risco
    
    Args:
        df (pandas.DataFrame): DataFrame com coluna 'risk_score'
        
    Returns:
        pandas.DataFrame: DataFrame com coluna 'leverage_suggestion' adicionada
    """
    df = df.copy()
    
    # Fórmula: leverage = max(1, 10 - (risk / 10))
    # Risco 0 → Alavancagem 10x
    # Risco 50 → Alavancagem 5x  
    # Risco 100 → Alavancagem 1x
    df['leverage_suggestion'] = np.maximum(1, 10 - (df['risk_score'] / 10))
    
    # Arredondar para 1 casa decimal
    df['leverage_suggestion'] = df['leverage_suggestion'].round(1)
    
    return df

def get_leverage_category(leverage):
    """
    Retorna categoria baseada no nível de alavancagem
    """
    if leverage >= 8:
        return "Alta"
    elif leverage >= 5:
        return "Média"
    elif leverage >= 3:
        return "Baixa"
    else:
        return "Mínima"