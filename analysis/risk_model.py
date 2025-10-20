import pandas as pd
import numpy as np

def calculate_risk_score(df):
    """
    Calcula uma pontuação de risco de 0-100 para cada moeda
    baseada em volatilidade, volume/market_cap e outras métricas
    
    Args:
        df (pandas.DataFrame): DataFrame com dados das moedas
        
    Returns:
        pandas.DataFrame: DataFrame com coluna 'risk_score' adicionada
    """
    df = df.copy()
    
    # Normalizar e tratar valores missing
    df['price_change_percentage_24h'] = df['price_change_percentage_24h'].fillna(0)
    df['total_volume'] = df['total_volume'].fillna(0)
    df['market_cap'] = df['market_cap'].fillna(1)  # Evitar divisão por zero
    
    # 1. Volatilidade (40% do score)
    volatility_score = calculate_volatility_score(df)
    
    # 2. Liquidez - Volume/MarketCap Ratio (30% do score)
    liquidity_score = calculate_liquidity_score(df)
    
    # 3. Tamanho do Mercado - Market Cap (30% do score)
    market_size_score = calculate_market_size_score(df)
    
    # Combinar scores com pesos
    risk_score = (
        volatility_score * 0.4 +
        liquidity_score * 0.3 +
        market_size_score * 0.3
    )
    
    # Garantir que o score está entre 0-100
    df['risk_score'] = np.clip(risk_score, 0, 100).round(1)
    
    return df

def calculate_volatility_score(df):
    """
    Calcula score baseado na volatilidade (mudança percentual 24h)
    Quanto maior a volatilidade, maior o risco
    """
    price_change = df['price_change_percentage_24h'].abs()
    
    # Normalizar para 0-100
    max_volatility = price_change.max()
    if max_volatility > 0:
        volatility_score = (price_change / max_volatility) * 100
    else:
        volatility_score = pd.Series([0] * len(df))
    
    return volatility_score

def calculate_liquidity_score(df):
    """
    Calcula score baseado na liquidez (Volume/MarketCap)
    Quanto menor a liquidez, maior o risco
    """
    # Calcular ratio volume/market_cap
    volume_ratio = df['total_volume'] / df['market_cap']
    
    # Inverter: menor liquidez = maior risco
    # Normalizar para 0-100
    max_ratio = volume_ratio.max()
    if max_ratio > 0:
        liquidity_risk = (1 - (volume_ratio / max_ratio)) * 100
    else:
        liquidity_risk = pd.Series([100] * len(df))  # Máximo risco se não há volume
    
    return liquidity_risk

def calculate_market_size_score(df):
    """
    Calcula score baseado no market cap
    Quanto menor o market cap, maior o risco
    """
    market_cap = df['market_cap']
    
    # Inverter: menor market cap = maior risco
    # Normalizar para 0-100
    max_mcap = market_cap.max()
    if max_mcap > 0:
        size_risk = (1 - (market_cap / max_mcap)) * 100
    else:
        size_risk = pd.Series([100] * len(df))
    
    return size_risk