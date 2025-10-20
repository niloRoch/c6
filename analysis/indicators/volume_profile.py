import pandas as pd
import numpy as np
import streamlit as st
from typing import Tuple, Dict

def calculate_volume_spike(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula spikes de volume comparando com média histórica
    
    Args:
        df: DataFrame com dados das moedas
    
    Returns:
        DataFrame com coluna 'volume_spike' adicionada
    """
    df = df.copy()
    
    # Calcular volume médio (assumindo que o volume atual representa últimas 24h)
    # Volume spike = volume_atual / volume_médio
    
    if 'total_volume' not in df.columns:
        df['volume_spike'] = 1.0
        return df
    
    # Calcular média de volume do mercado
    avg_volume = df['total_volume'].median()
    
    volume_spikes = []
    volume_percentiles = []
    
    for idx, row in df.iterrows():
        current_volume = row['total_volume']
        market_cap = row.get('market_cap', 1)
        
        # Normalizar volume pelo market cap para comparação justa
        volume_to_mcap_ratio = (current_volume / market_cap) if market_cap > 0 else 0
        
        # Calcular spike baseado em múltiplos fatores
        # 1. Volume absoluto vs média
        volume_vs_avg = current_volume / avg_volume if avg_volume > 0 else 1
        
        # 2. Volume/Market Cap ratio (quanto maior, mais líquido)
        expected_ratio = 0.1  # 10% é considerado normal
        ratio_multiplier = volume_to_mcap_ratio / expected_ratio if expected_ratio > 0 else 1
        
        # Score combinado de spike
        spike_score = (volume_vs_avg * 0.7) + (ratio_multiplier * 0.3)
        
        volume_spikes.append(spike_score)
        
        # Calcular percentil de volume
        percentile = (df['total_volume'] <= current_volume).sum() / len(df) * 100
        volume_percentiles.append(percentile)
    
    df['volume_spike'] = volume_spikes
    df['volume_percentile'] = volume_percentiles
    
    # Classificar intensidade do spike
    df['volume_spike_level'] = df['volume_spike'].apply(classify_volume_spike)
    
    return df

def classify_volume_spike(spike_value: float) -> str:
    """Classifica o nível do spike de volume"""
    if spike_value >= 3.0:
        return "🔥 EXTREMO"
    elif spike_value >= 2.0:
        return "🚀 MUITO ALTO"
    elif spike_value >= 1.5:
        return "📈 ALTO"
    elif spike_value >= 1.2:
        return "📊 MODERADO"
    else:
        return "➡️ NORMAL"

def calculate_volume_profile(high: pd.Series, low: pd.Series, volume: pd.Series, 
                           price_levels: int = 20) -> Dict:
    """
    Calcula o Volume Profile - análise de volume por nível de preço
    
    Args:
        high: Série com preços máximos
        low: Série com preços mínimos  
        volume: Série com volumes
        price_levels: Número de níveis de preço para análise
    
    Returns:
        Dict com POC, VAH, VAL, volume por nível
    """
    try:
        if len(high) == 0 or len(low) == 0 or len(volume) == 0:
            return {}
        
        min_price = low.min()
        max_price = high.max()
        
        if min_price == max_price:
            return {}
        
        # Criar níveis de preço
        price_range = np.linspace(min_price, max_price, price_levels)
        
        # Calcular volume por nível de preço
        volume_at_price = {}
        
        for i in range(len(high)):
            for level in price_range:
                if low.iloc[i] <= level <= high.iloc[i]:
                    if level in volume_at_price:
                        volume_at_price[level] += volume.iloc[i]
                    else:
                        volume_at_price[level] = volume.iloc[i]
        
        if not volume_at_price:
            return {}
        
        # POC (Point of Control) - nível com maior volume
        poc_price = max(volume_at_price, key=volume_at_price.get)
        total_volume = sum(volume_at_price.values())
        
        # Value Area (70% do volume)
        sorted_levels = sorted(volume_at_price.items(), key=lambda x: x[1], reverse=True)
        
        cumulative_volume = 0
        value_area_levels = []
        
        for level, vol in sorted_levels:
            cumulative_volume += vol
            value_area_levels.append(level)
            if cumulative_volume >= total_volume * 0.7:
                break
        
        vah = max(value_area_levels)  # Value Area High
        val = min(value_area_levels)  # Value Area Low
        
        return {
            'poc': poc_price,
            'vah': vah,
            'val': val,
            'total_volume': total_volume,
            'value_area_volume': cumulative_volume,
            'volume_profile': volume_at_price,
            'price_range_min': min_price,
            'price_range_max': max_price,
            'value_area_percentage': (cumulative_volume / total_volume) * 100
        }
        
    except Exception as e:
        return {}

def volume_profile_signal(current_price: float, volume_profile_data: Dict) -> str:
    """
    Gera sinal baseado no Volume Profile
    
    Args:
        current_price: Preço atual
        volume_profile_data: Dados do volume profile
    
    Returns:
        String com sinal
    """
    if not volume_profile_data:
        return "NEUTRO"
    
    poc = volume_profile_data.get('poc', 0)
    vah = volume_profile_data.get('vah', 0)
    val = volume_profile_data.get('val', 0)
    
    if current_price < val:
        return "🟢 COMPRA FORTE"  # Preço abaixo da área de valor
    elif current_price > vah:
        return "🔴 VENDA FORTE"   # Preço acima da área de valor
    elif abs(current_price - poc) / poc < 0.02:  # Dentro de 2% do POC
        return "⚪ POC - NEUTRO"
    elif current_price < poc:
        return "🟢 COMPRA"
    elif current_price > poc:
        return "🔴 VENDA"
    else:
        return "⚪ NEUTRO"

def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, 
                  volume: pd.Series) -> pd.Series:
    """
    Calcula VWAP (Volume Weighted Average Price)
    
    Args:
        high: Preços máximos
        low: Preços mínimos
        close: Preços de fechamento
        volume: Volumes
    
    Returns:
        Série com VWAP
    """
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap

def calculate_volume_trend(volumes: pd.Series, period: int = 14) -> Dict:
    """
    Calcula tendência de volume
    
    Args:
        volumes: Série de volumes
        period: Período para análise
    
    Returns:
        Dict com informações de tendência
    """
    if len(volumes) < period:
        return {'trend': 'INSUFICIENTE', 'strength': 0}
    
    recent_avg = volumes.tail(period // 2).mean()
    older_avg = volumes.head(period // 2).mean()
    
    if older_avg == 0:
        return {'trend': 'INDEFINIDO', 'strength': 0}
    
    change_pct = ((recent_avg - older_avg) / older_avg) * 100
    
    if change_pct > 50:
        trend = "📈 CRESCENTE FORTE"
        strength = min(100, change_pct)
    elif change_pct > 20:
        trend = "📈 CRESCENTE"
        strength = change_pct
    elif change_pct < -50:
        trend = "📉 DECRESCENTE FORTE"
        strength = min(100, abs(change_pct))
    elif change_pct < -20:
        trend = "📉 DECRESCENTE"
        strength = abs(change_pct)
    else:
        trend = "➡️ ESTÁVEL"
        strength = 0
    
    return {
        'trend': trend,
        'strength': strength,
        'change_pct': change_pct
    }

def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Calcula OBV (On-Balance Volume)
    
    Args:
        close: Preços de fechamento
        volume: Volumes
    
    Returns:
        Série com OBV
    """
    obv = pd.Series(index=close.index, dtype=float)
    obv.iloc[0] = volume.iloc[0]
    
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i-1]
    
    return obv

def volume_based_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica todos os indicadores baseados em volume ao DataFrame
    
    Args:
        df: DataFrame com dados das criptomoedas
    
    Returns:
        DataFrame com colunas adicionais dos indicadores
    """
    df = df.copy()
    
    # Calcular VWAP simplificado
    if all(col in df.columns for col in ['high_24h', 'low_24h', 'current_price', 'total_volume']):
        vwaps = []
        for idx, row in df.iterrows():
            typical_price = (row['high_24h'] + row['low_24h'] + row['current_price']) / 3
            vwaps.append(typical_price)
        df['vwap'] = vwaps
    
    # Calcular Volume Profile simplificado
    volume_profile_signals = []
    volume_profile_strength = []
    poc_distances = []
    
    for idx, row in df.iterrows():
        high = pd.Series([row['high_24h']])
        low = pd.Series([row['low_24h']])
        volume = pd.Series([row['total_volume']])
        
        vp_data = calculate_volume_profile(high, low, volume, price_levels=10)
        signal = volume_profile_signal(row['current_price'], vp_data)
        
        volume_profile_signals.append(signal)
        
        # Calcular força do sinal
        if vp_data and 'poc' in vp_data:
            distance_from_poc = abs(row['current_price'] - vp_data['poc']) / vp_data['poc']
            strength = min(100, distance_from_poc * 500)
            poc_distances.append(distance_from_poc * 100)
        else:
            strength = 0
            poc_distances.append(0)
        
        volume_profile_strength.append(strength)
    
    df['volume_profile_signal'] = volume_profile_signals
    df['volume_profile_strength'] = volume_profile_strength
    df['poc_distance_pct'] = poc_distances
    
    # Calcular volume relativo
    if 'total_volume' in df.columns:
        median_volume = df['total_volume'].median()
        df['volume_ratio'] = df['total_volume'] / median_volume
        
        # Classificar volume
        df['volume_classification'] = df['volume_ratio'].apply(
            lambda x: "🔥 MUITO ALTO" if x > 2 else 
                     "📈 ALTO" if x > 1.5 else 
                     "📊 NORMAL" if x > 0.5 else 
                     "📉 BAIXO"
        )
    
    # Adicionar indicadores de liquidez
    df['liquidity_score'] = (df['total_volume'] / df['market_cap']) * 100
    df['liquidity_rating'] = df['liquidity_score'].apply(
        lambda x: "⭐⭐⭐⭐⭐" if x > 20 else
                 "⭐⭐⭐⭐" if x > 10 else
                 "⭐⭐⭐" if x > 5 else
                 "⭐⭐" if x > 2 else
                 "⭐"
    )
    
    return df

def detect_volume_anomalies(df: pd.DataFrame, std_threshold: float = 2.5) -> pd.DataFrame:
    """
    Detecta anomalias no volume usando desvio padrão
    
    Args:
        df: DataFrame com dados
        std_threshold: Número de desvios padrão para considerar anomalia
    
    Returns:
        DataFrame com coluna 'volume_anomaly'
    """
    df = df.copy()
    
    if 'total_volume' not in df.columns:
        df['volume_anomaly'] = False
        return df
    
    volume_mean = df['total_volume'].mean()
    volume_std = df['total_volume'].std()
    
    # Detectar outliers
    df['volume_anomaly'] = df['total_volume'] > (volume_mean + std_threshold * volume_std)
    df['volume_z_score'] = (df['total_volume'] - volume_mean) / volume_std if volume_std > 0 else 0
    
    return df

def calculate_volume_momentum(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula momentum de volume (taxa de mudança)
    
    Args:
        df: DataFrame com dados
    
    Returns:
        DataFrame com coluna 'volume_momentum'
    """
    df = df.copy()
    
    # Como temos apenas snapshot, usar volume vs market cap como proxy
    if 'total_volume' in df.columns and 'market_cap' in df.columns:
        df['volume_momentum'] = (df['total_volume'] / df['market_cap']) * 100
        
        df['volume_momentum_level'] = df['volume_momentum'].apply(
            lambda x: "🚀 EXTREMO" if x > 30 else
                     "📈 ALTO" if x > 15 else
                     "➡️ MODERADO" if x > 5 else
                     "📉 BAIXO"
        )
    
    return df