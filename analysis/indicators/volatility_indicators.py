import pandas as pd
import numpy as np
import streamlit as st

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """
    Calcula ATR (Average True Range)
    
    Args:
        high: Série de preços máximos
        low: Série de preços mínimos
        close: Série de preços de fechamento
        period: Período do ATR
    
    Returns:
        Valor do ATR
    """
    if len(close) < period + 1:
        return 0.0
    
    # Calcular True Range
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # Calcular ATR (média móvel do True Range)
    atr = true_range.rolling(window=period).mean()
    
    return atr.iloc[-1] if not np.isnan(atr.iloc[-1]) else 0.0

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> dict:
    """
    Calcula Bandas de Bollinger
    
    Args:
        prices: Série de preços
        period: Período da média móvel
        std_dev: Número de desvios padrão
    
    Returns:
        Dict com upper_band, middle_band, lower_band
    """
    if len(prices) < period:
        return {
            'upper': prices.iloc[-1] if len(prices) > 0 else 0,
            'middle': prices.iloc[-1] if len(prices) > 0 else 0,
            'lower': prices.iloc[-1] if len(prices) > 0 else 0,
            'width': 0
        }
    
    # Média móvel simples
    middle_band = prices.rolling(window=period).mean()
    
    # Desvio padrão
    std = prices.rolling(window=period).std()
    
    # Bandas superior e inferior
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    # Largura das bandas (normalizada)
    width = ((upper_band - lower_band) / middle_band) * 100
    
    return {
        'upper': upper_band.iloc[-1],
        'middle': middle_band.iloc[-1],
        'lower': lower_band.iloc[-1],
        'width': width.iloc[-1] if not np.isnan(width.iloc[-1]) else 0
    }

def get_bb_position(current_price: float, bb_data: dict) -> float:
    """
    Calcula posição do preço nas Bandas de Bollinger (0 a 1)
    0 = banda inferior, 0.5 = média, 1 = banda superior
    """
    upper = bb_data['upper']
    lower = bb_data['lower']
    
    if upper == lower:
        return 0.5
    
    position = (current_price - lower) / (upper - lower)
    return max(0, min(1, position))

def get_bb_signal(position: float, width: float) -> str:
    """
    Retorna sinal baseado na posição nas Bandas de Bollinger
    """
    if position < 0.2:
        return "SOBREVENDIDO"
    elif position > 0.8:
        return "SOBRECOMPRADO"
    elif 0.4 <= position <= 0.6:
        return "NEUTRO"
    elif position < 0.5:
        return "BAIXA"
    else:
        return "ALTA"

def calculate_historical_volatility(prices: pd.Series, period: int = 30) -> float:
    """
    Calcula volatilidade histórica (desvio padrão dos retornos)
    
    Args:
        prices: Série de preços
        period: Período para cálculo
    
    Returns:
        Volatilidade em percentual
    """
    if len(prices) < 2:
        return 0.0
    
    # Calcular retornos logarítmicos
    returns = np.log(prices / prices.shift(1))
    
    # Calcular volatilidade (desvio padrão anualizado)
    volatility = returns.rolling(window=period).std() * np.sqrt(365) * 100
    
    return volatility.iloc[-1] if not np.isnan(volatility.iloc[-1]) else 0.0

def calculate_keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series, 
                               period: int = 20, atr_mult: float = 2.0) -> dict:
    """
    Calcula Canais de Keltner
    
    Args:
        high: Série de preços máximos
        low: Série de preços mínimos
        close: Série de preços de fechamento
        period: Período da EMA
        atr_mult: Multiplicador do ATR
    
    Returns:
        Dict com upper, middle, lower
    """
    if len(close) < period:
        current = close.iloc[-1] if len(close) > 0 else 0
        return {'upper': current, 'middle': current, 'lower': current}
    
    # Linha central (EMA)
    middle = close.ewm(span=period, adjust=False).mean()
    
    # Calcular ATR
    atr = calculate_atr(high, low, close, period)
    
    # Canais
    upper = middle + (atr * atr_mult)
    lower = middle - (atr * atr_mult)
    
    return {
        'upper': upper.iloc[-1],
        'middle': middle.iloc[-1],
        'lower': lower.iloc[-1]
    }

def calculate_volatility_ratio(current_volatility: float, avg_volatility: float) -> float:
    """
    Calcula ratio de volatilidade atual vs média
    """
    if avg_volatility == 0:
        return 1.0
    
    return current_volatility / avg_volatility

def get_volatility_level(volatility: float) -> str:
    """
    Classifica o nível de volatilidade
    """
    if volatility < 20:
        return "MUITO BAIXA"
    elif volatility < 40:
        return "BAIXA"
    elif volatility < 60:
        return "MODERADA"
    elif volatility < 80:
        return "ALTA"
    else:
        return "MUITO ALTA"

def calculate_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de volatilidade para todo o DataFrame
    """
    df = df.copy()
    
    # Listas para armazenar resultados
    atr_values = []
    atr_percentages = []
    bb_positions = []
    bb_signals = []
    bb_widths = []
    volatility_levels = []
    volatility_scores = []
    
    for idx, row in df.iterrows():
        try:
            # Obter dados
            current_price = row['current_price']
            high_24h = row['high_24h']
            low_24h = row['low_24h']
            price_change = row.get('price_change_percentage_24h', 0)
            
            # Criar séries sintéticas
            prices = []
            highs = []
            lows = []
            
            for i in range(30):
                progress = i / 30
                estimated_change = price_change * progress
                base_price = current_price / (1 + price_change / 100)
                estimated_price = base_price * (1 + estimated_change / 100)
                
                # Adicionar variação
                noise = np.random.uniform(-0.02, 0.02)
                estimated_price *= (1 + noise)
                
                prices.append(estimated_price)
                highs.append(estimated_price * 1.01)
                lows.append(estimated_price * 0.99)
            
            price_series = pd.Series(prices)
            high_series = pd.Series(highs)
            low_series = pd.Series(lows)
            
            # Calcular ATR
            atr = calculate_atr(high_series, low_series, price_series)
            atr_pct = (atr / current_price) * 100 if current_price > 0 else 0
            
            atr_values.append(atr)
            atr_percentages.append(atr_pct)
            
            # Calcular Bandas de Bollinger
            bb_data = calculate_bollinger_bands(price_series)
            bb_position = get_bb_position(current_price, bb_data)
            bb_signal = get_bb_signal(bb_position, bb_data['width'])
            
            bb_positions.append(bb_position)
            bb_signals.append(bb_signal)
            bb_widths.append(bb_data['width'])
            
            # Calcular volatilidade histórica
            hist_vol = calculate_historical_volatility(price_series)
            vol_level = get_volatility_level(hist_vol)
            
            volatility_levels.append(vol_level)
            
            # Score de volatilidade (0-100, menor é melhor)
            # Baseado em ATR% e largura das BB
            vol_score = min(100, (atr_pct * 10) + (bb_data['width'] * 2))
            volatility_scores.append(vol_score)
            
        except Exception as e:
            # Valores padrão em caso de erro
            atr_values.append(0)
            atr_percentages.append(0)
            bb_positions.append(0.5)
            bb_signals.append("NEUTRO")
            bb_widths.append(0)
            volatility_levels.append("BAIXA")
            volatility_scores.append(50)
    
    # Adicionar colunas ao DataFrame
    df['atr'] = atr_values
    df['atr_pct'] = atr_percentages
    df['bb_position'] = bb_positions
    df['bb_signal'] = bb_signals
    df['bb_width'] = bb_widths
    df['volatility_level'] = volatility_levels
    df['volatility_score'] = volatility_scores
    
    return df

def format_volatility_display(row) -> str:
    """
    Formata indicadores de volatilidade para exibição
    """
    if 'atr_pct' not in row or 'bb_position' not in row:
        return "N/A"
    
    atr_pct = row['atr_pct']
    bb_pos = row['bb_position']
    bb_signal = row.get('bb_signal', 'NEUTRO')
    
    # Ícones baseados em valores
    if atr_pct < 2:
        vol_icon = "🟢"  # Baixa volatilidade
    elif atr_pct < 5:
        vol_icon = "🟡"  # Média volatilidade
    else:
        vol_icon = "🔴"  # Alta volatilidade
    
    if bb_pos < 0.3:
        bb_icon = "⬇️"
    elif bb_pos > 0.7:
        bb_icon = "⬆️"
    else:
        bb_icon = "↔️"
    
    return f"ATR:{atr_pct:.1f}%{vol_icon} BB:{bb_pos:.2f}{bb_icon}"

def calculate_squeeze_momentum(bb_data: dict, keltner_data: dict) -> str:
    """
    Detecta TTM Squeeze (Bandas de Bollinger dentro dos Canais de Keltner)
    """
    bb_width = bb_data['upper'] - bb_data['lower']
    kc_width = keltner_data['upper'] - keltner_data['lower']
    
    if bb_width < kc_width:
        return "SQUEEZE ON"  # Consolidação - possível explosão
    else:
        return "SQUEEZE OFF"  # Expansão normal

def get_volatility_trend(volatilities: list) -> str:
    """
    Determina tendência de volatilidade
    """
    if len(volatilities) < 3:
        return "ESTÁVEL"
    
    recent = volatilities[-3:]
    if all(recent[i] > recent[i-1] for i in range(1, len(recent))):
        return "CRESCENTE"
    elif all(recent[i] < recent[i-1] for i in range(1, len(recent))):
        return "DECRESCENTE"
    else:
        return "ESTÁVEL"