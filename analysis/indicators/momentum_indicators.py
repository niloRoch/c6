import pandas as pd
import numpy as np
import streamlit as st

def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """
    Calcula RSI (Relative Strength Index)
    
    Args:
        prices: Série de preços
        period: Período do RSI (padrão: 14)
    
    Returns:
        Valor do RSI (0-100)
    """
    if len(prices) < period + 1:
        return 50.0  # Valor neutro se não houver dados suficientes
    
    # Calcular mudanças de preço
    delta = prices.diff()
    
    # Separar ganhos e perdas
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Calcular médias
    avg_gain = gains.rolling(window=period, min_periods=period).mean()
    avg_loss = losses.rolling(window=period, min_periods=period).mean()
    
    # Calcular RS e RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50.0

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """
    Calcula MACD (Moving Average Convergence Divergence)
    
    Args:
        prices: Série de preços
        fast: Período EMA rápida
        slow: Período EMA lenta
        signal: Período da linha de sinal
    
    Returns:
        Dict com MACD, Signal e Histograma
    """
    if len(prices) < slow + signal:
        return {'macd': 0, 'signal': 0, 'histogram': 0}
    
    # Calcular EMAs
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    
    # MACD = EMA rápida - EMA lenta
    macd_line = ema_fast - ema_slow
    
    # Linha de sinal = EMA de 9 períodos do MACD
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    # Histograma = MACD - Signal
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line.iloc[-1],
        'signal': signal_line.iloc[-1],
        'histogram': histogram.iloc[-1]
    }

def get_rsi_signal(rsi: float) -> str:
    """
    Retorna sinal baseado no RSI
    """
    if rsi < 30:
        return "SOBREVENDA"
    elif rsi > 70:
        return "SOBRECOMPRA"
    elif 45 <= rsi <= 55:
        return "NEUTRO"
    elif rsi < 45:
        return "BEARISH"
    else:
        return "BULLISH"

def get_macd_signal(macd_data: dict) -> str:
    """
    Retorna sinal baseado no MACD
    """
    histogram = macd_data['histogram']
    
    if histogram > 0:
        return "COMPRA"
    elif histogram < 0:
        return "VENDA"
    else:
        return "NEUTRO"

def calculate_momentum_score(rsi: float, macd_data: dict) -> int:
    """
    Calcula score de momentum (0-100)
    """
    # Score baseado no RSI
    if rsi < 30:
        rsi_score = 100  # Sobrevenda = oportunidade
    elif rsi > 70:
        rsi_score = 0    # Sobrecompra = risco
    else:
        rsi_score = 50 + (50 - rsi) * 0.5
    
    # Score baseado no MACD
    histogram = macd_data['histogram']
    if abs(histogram) > 0:
        macd_score = 50 + (histogram * 10)
    else:
        macd_score = 50
    
    # Limitar entre 0-100
    macd_score = max(0, min(100, macd_score))
    
    # Score final (média ponderada)
    final_score = (rsi_score * 0.6) + (macd_score * 0.4)
    
    return int(final_score)

def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> dict:
    """
    Calcula Oscilador Estocástico
    
    Returns:
        Dict com %K e %D
    """
    if len(close) < period:
        return {'k': 50, 'd': 50}
    
    # %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    
    k_percent = ((close - lowest_low) / (highest_high - lowest_low)) * 100
    
    # %D = Média móvel de 3 períodos de %K
    d_percent = k_percent.rolling(window=3).mean()
    
    return {
        'k': k_percent.iloc[-1] if not np.isnan(k_percent.iloc[-1]) else 50,
        'd': d_percent.iloc[-1] if not np.isnan(d_percent.iloc[-1]) else 50
    }

def get_stochastic_signal(stoch_data: dict) -> str:
    """
    Retorna sinal baseado no Estocástico
    """
    k = stoch_data['k']
    d = stoch_data['d']
    
    if k < 20 and d < 20:
        return "SOBREVENDA"
    elif k > 80 and d > 80:
        return "SOBRECOMPRA"
    elif k > d and k > 50:
        return "COMPRA"
    elif k < d and k < 50:
        return "VENDA"
    else:
        return "NEUTRO"

def calculate_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de momentum para todo o DataFrame
    Usa dados de 24h como aproximação
    """
    df = df.copy()
    
    # Listas para armazenar resultados
    rsi_values = []
    macd_signals = []
    momentum_scores = []
    stoch_signals = []
    
    for idx, row in df.iterrows():
        try:
            # Criar série de preços sintética baseada em high, low, current
            # Aproximação: usar variação 24h para estimar comportamento
            current_price = row['current_price']
            high_24h = row['high_24h']
            low_24h = row['low_24h']
            price_change = row.get('price_change_percentage_24h', 0)
            
            # Criar série sintética de 30 pontos
            prices = []
            highs = []
            lows = []
            
            # Simular preços baseado na tendência
            for i in range(30):
                # Interpolação linear da variação
                progress = i / 30
                estimated_change = price_change * progress
                base_price = current_price / (1 + price_change / 100)
                estimated_price = base_price * (1 + estimated_change / 100)
                
                # Adicionar variação aleatória pequena
                noise = np.random.uniform(-0.01, 0.01)
                estimated_price *= (1 + noise)
                
                prices.append(estimated_price)
                highs.append(estimated_price * 1.005)
                lows.append(estimated_price * 0.995)
            
            price_series = pd.Series(prices)
            high_series = pd.Series(highs)
            low_series = pd.Series(lows)
            
            # Calcular RSI
            rsi = calculate_rsi(price_series)
            rsi_values.append(rsi)
            
            # Calcular MACD
            macd_data = calculate_macd(price_series)
            macd_signal = get_macd_signal(macd_data)
            macd_signals.append(macd_signal)
            
            # Calcular Score de Momentum
            momentum_score = calculate_momentum_score(rsi, macd_data)
            momentum_scores.append(momentum_score)
            
            # Calcular Estocástico
            stoch_data = calculate_stochastic(high_series, low_series, price_series)
            stoch_signal = get_stochastic_signal(stoch_data)
            stoch_signals.append(stoch_signal)
            
        except Exception as e:
            # Em caso de erro, usar valores padrão
            rsi_values.append(50)
            macd_signals.append("NEUTRO")
            momentum_scores.append(50)
            stoch_signals.append("NEUTRO")
    
    # Adicionar colunas ao DataFrame
    df['rsi'] = rsi_values
    df['macd_signal'] = macd_signals
    df['momentum_score'] = momentum_scores
    df['stochastic_signal'] = stoch_signals
    
    # Adicionar sinal RSI categorizado
    df['rsi_signal'] = df['rsi'].apply(get_rsi_signal)
    
    return df

def format_momentum_display(row) -> str:
    """
    Formata indicadores de momentum para exibição
    """
    if 'rsi' not in row or 'macd_signal' not in row:
        return "N/A"
    
    rsi = row['rsi']
    macd = row['macd_signal']
    
    # Ícones baseados em valores
    if rsi < 30:
        rsi_icon = "🟢"  # Sobrevenda
    elif rsi > 70:
        rsi_icon = "🔴"  # Sobrecompra
    else:
        rsi_icon = "⚪"
    
    if macd == "COMPRA":
        macd_icon = "📈"
    elif macd == "VENDA":
        macd_icon = "📉"
    else:
        macd_icon = "➡️"
    
    return f"RSI:{rsi:.0f}{rsi_icon} MACD:{macd_icon}"