import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple, Optional
import requests
from datetime import datetime, timedelta
import time

def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calcula Média Móvel Exponencial (EMA)"""
    return prices.ewm(span=period, adjust=False).mean()

def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """Calcula Média Móvel Simples (SMA)"""
    return prices.rolling(window=period).mean()

@st.cache_data(ttl=600)
def get_historical_data_4h(coin_id: str, queue_manager=None) -> pd.DataFrame:
    """
    Obtém dados históricos da CoinGecko com suporte a queue manager
    
    Args:
        coin_id: ID da moeda
        queue_manager: Gerenciador de fila (opcional)
    
    Returns:
        DataFrame com dados históricos
    """
    cache_key = f"historical_4h_{coin_id}"
    
    # Se tem queue manager, usar ele
    if queue_manager:
        cached = queue_manager.get_from_cache(cache_key, ttl=600)
        if cached is not None and not cached.empty:
            return cached
    
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': 90,
            'interval': 'daily'
        }
        
        # Usar queue manager se disponível
        if queue_manager:
            def fetch_data():
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                return response.json()
            
            data = queue_manager.execute_with_retry(fetch_data, cache_key, max_retries=2)
        else:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        
        if data is None or 'prices' not in data:
            return pd.DataFrame()
        
        prices = data.get('prices', [])
        if not prices:
            return pd.DataFrame()
        
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # Cachear se tem queue manager
        if queue_manager and not df.empty:
            queue_manager.set_cache(cache_key, df)
        
        return df
        
    except Exception as e:
        st.warning(f"⚠️ Erro ao obter dados para {coin_id}: {str(e)[:100]}")
        return pd.DataFrame()

def resample_to_4h(df: pd.DataFrame) -> pd.DataFrame:
    """Realiza resample dos dados para 4h"""
    if df.empty:
        return pd.DataFrame()
    
    try:
        four_hourly = df['price'].resample('4H').ohlc()
        four_hourly['volume'] = df['price'].resample('4H').count()
        four_hourly = four_hourly.dropna()
        return four_hourly
    except Exception as e:
        return pd.DataFrame()

def analyze_ma_touch_4h(data: pd.DataFrame, current_price: float) -> Dict:
    """
    Analisa se o preço tocou a MA 200 no gráfico de 4h
    
    Args:
        data: DataFrame com dados OHLC de 4h
        current_price: Preço atual
    
    Returns:
        Dict com análise detalhada
    """
    if data.empty or len(data) < 50:
        return {}
    
    try:
        close_prices = data['close']
        high_prices = data['high']
        low_prices = data['low']
        
        # Calcular período baseado nos dados disponíveis
        period = min(200, len(close_prices) - 1)
        if period < 50:
            return {}
        
        # Calcular médias móveis
        sma_200 = calculate_sma(close_prices, period)
        ema_200 = calculate_ema(close_prices, period)
        
        # Últimos valores
        last_sma = sma_200.iloc[-1] if not sma_200.empty else None
        last_ema = ema_200.iloc[-1] if not ema_200.empty else None
        
        if last_sma is None or last_ema is None:
            return {}
        
        # Verificar toque nas médias nos últimos 3 candles
        recent_touches_sma = False
        recent_touches_ema = False
        touch_type_sma = "NENHUM"
        touch_type_ema = "NENHUM"
        touch_strength_sma = 0
        touch_strength_ema = 0
        
        # Analisar últimos 3 candles
        for i in range(max(-3, -len(data)), 0):
            high = high_prices.iloc[i]
            low = low_prices.iloc[i]
            close = data['close'].iloc[i]
            
            # SMA Touch Analysis
            if not pd.isna(sma_200.iloc[i]):
                sma_val = sma_200.iloc[i]
                if low <= sma_val <= high:
                    recent_touches_sma = True
                    
                    # Determinar tipo de toque
                    if close > sma_val:
                        touch_type_sma = "COMPRA"
                        # Força baseada em quão acima fechou
                        touch_strength_sma = max(touch_strength_sma, 
                                                 ((close - sma_val) / sma_val) * 100)
                    else:
                        touch_type_sma = "VENDA"
                        touch_strength_sma = max(touch_strength_sma,
                                                ((sma_val - close) / sma_val) * 100)
            
            # EMA Touch Analysis
            if not pd.isna(ema_200.iloc[i]):
                ema_val = ema_200.iloc[i]
                if low <= ema_val <= high:
                    recent_touches_ema = True
                    
                    if close > ema_val:
                        touch_type_ema = "COMPRA"
                        touch_strength_ema = max(touch_strength_ema,
                                                ((close - ema_val) / ema_val) * 100)
                    else:
                        touch_type_ema = "VENDA"
                        touch_strength_ema = max(touch_strength_ema,
                                                ((ema_val - close) / ema_val) * 100)
        
        # Distâncias percentuais
        distance_to_sma = ((current_price - last_sma) / last_sma) * 100
        distance_to_ema = ((current_price - last_ema) / last_ema) * 100
        
        # Tendência
        trend_sma = "ALTA" if current_price > last_sma else "BAIXA"
        trend_ema = "ALTA" if current_price > last_ema else "BAIXA"
        
        # Verificar se está próximo (dentro de 2%)
        near_sma = abs(distance_to_sma) < 2
        near_ema = abs(distance_to_ema) < 2
        
        # Inclinação das MAs (últimos 5 períodos)
        if len(sma_200) >= 5:
            sma_slope = (sma_200.iloc[-1] - sma_200.iloc[-5]) / sma_200.iloc[-5] * 100
            ema_slope = (ema_200.iloc[-1] - ema_200.iloc[-5]) / ema_200.iloc[-5] * 100
        else:
            sma_slope = 0
            ema_slope = 0
        
        return {
            'timeframe': '4h',
            'sma_200': last_sma,
            'ema_200': last_ema,
            'touched_sma': recent_touches_sma,
            'touched_ema': recent_touches_ema,
            'touch_type_sma': touch_type_sma,
            'touch_type_ema': touch_type_ema,
            'touch_strength_sma': round(touch_strength_sma, 2),
            'touch_strength_ema': round(touch_strength_ema, 2),
            'near_sma': near_sma,
            'near_ema': near_ema,
            'distance_sma_pct': round(distance_to_sma, 2),
            'distance_ema_pct': round(distance_to_ema, 2),
            'trend_sma': trend_sma,
            'trend_ema': trend_ema,
            'sma_slope': round(sma_slope, 2),
            'ema_slope': round(ema_slope, 2),
            'periods_used': period,
            'data_points': len(data)
        }
        
    except Exception as e:
        st.warning(f"Erro na análise de MA 4h: {e}")
        return {}

def multi_timeframe_ma_analysis(coin_id: str, current_price: float, 
                                queue_manager=None) -> Dict[str, Dict]:
    """
    Realiza análise de médias móveis focada em 4h
    
    Args:
        coin_id: ID da moeda
        current_price: Preço atual
        queue_manager: Gerenciador de fila (opcional)
    
    Returns:
        Dict com análise de 4h
    """
    historical_data = get_historical_data_4h(coin_id, queue_manager)
    
    if historical_data.empty:
        return {'4h': {}}
    
    data_4h = resample_to_4h(historical_data)
    
    if data_4h.empty:
        return {'4h': {}}
    
    analysis_4h = analyze_ma_touch_4h(data_4h, current_price)
    
    return {'4h': analysis_4h}

def generate_ma_signal(ma_analysis: Dict[str, Dict]) -> Tuple[str, int]:
    """
    Gera sinal consolidado baseado na análise de MA 4h
    
    Args:
        ma_analysis: Dict com análise de MA
    
    Returns:
        Tuple (sinal, força)
    """
    if not ma_analysis or '4h' not in ma_analysis:
        return "SEM DADOS", 0
    
    analysis = ma_analysis['4h']
    
    if not analysis:
        return "SEM DADOS", 0
    
    # Extrair informações
    touched_sma = analysis.get('touched_sma', False)
    touched_ema = analysis.get('touched_ema', False)
    touch_type_sma = analysis.get('touch_type_sma', 'NENHUM')
    touch_type_ema = analysis.get('touch_type_ema', 'NENHUM')
    touch_strength_sma = analysis.get('touch_strength_sma', 0)
    touch_strength_ema = analysis.get('touch_strength_ema', 0)
    near_sma = analysis.get('near_sma', False)
    near_ema = analysis.get('near_ema', False)
    trend_sma = analysis.get('trend_sma', 'NEUTRO')
    sma_slope = analysis.get('sma_slope', 0)
    
    # Score inicial
    score = 50
    
    # Análise de toque
    if touched_sma and touch_type_sma == "COMPRA":
        score += 40
        if sma_slope > 0:  # MA subindo
            score += 10
        signal = "🟢 FORTE COMPRA"
    elif touched_ema and touch_type_ema == "COMPRA":
        score += 30
        signal = "🟢 COMPRA"
    elif (near_sma or near_ema) and trend_sma == "ALTA":
        score += 20
        signal = "🟢 COMPRA PRÓXIMA"
    elif touched_sma and touch_type_sma == "VENDA":
        score -= 40
        if sma_slope < 0:  # MA descendo
            score -= 10
        signal = "🔴 FORTE VENDA"
    elif touched_ema and touch_type_ema == "VENDA":
        score -= 30
        signal = "🔴 VENDA"
    elif (near_sma or near_ema) and trend_sma == "BAIXA":
        score -= 20
        signal = "🔴 VENDA PRÓXIMA"
    elif trend_sma == "ALTA":
        score += 10
        signal = "⬆️ TENDÊNCIA ALTA"
    elif trend_sma == "BAIXA":
        score -= 10
        signal = "⬇️ TENDÊNCIA BAIXA"
    else:
        signal = "⚪ NEUTRO"
    
    # Ajustar score baseado na força do toque
    if touched_sma:
        score += min(10, touch_strength_sma)
    if touched_ema:
        score += min(10, touch_strength_ema)
    
    # Limitar score entre 0-100
    score = max(0, min(100, score))
    
    return signal, int(score)

def calculate_ma_indicators(df: pd.DataFrame, queue_manager=None) -> pd.DataFrame:
    """
    Aplica análise de médias móveis 4h com suporte a queue manager
    Analisa apenas top 15 para otimizar requisições
    
    Args:
        df: DataFrame com dados das moedas
        queue_manager: Gerenciador de fila (opcional)
    
    Returns:
        DataFrame com indicadores MA adicionados
    """
    df = df.copy()
    
    ma_signals = []
    ma_strengths = []
    ma_details = []
    
    # Limitar para as top 15 moedas
    limited_df = df.head(15) if len(df) > 15 else df
    
    total_coins = len(limited_df)
    
    # Criar progress bar se não estiver em queue
    progress_text = st.empty()
    
    for idx, (_, row) in enumerate(limited_df.iterrows(), 1):
        coin_id = row.get('id', '') or row.get('coin_id', '')
        current_price = row.get('current_price', 0)
        
        if coin_id and current_price > 0:
            # Mostrar progresso
            if idx % 3 == 0:
                progress_text.text(f"📊 Analisando MA: {idx}/{total_coins} moedas...")
            
            # Análise multi-timeframe (apenas 4h)
            ma_analysis = multi_timeframe_ma_analysis(coin_id, current_price, queue_manager)
            
            # Gerar sinal consolidado
            signal, strength = generate_ma_signal(ma_analysis)
            
            ma_signals.append(signal)
            ma_strengths.append(strength)
            ma_details.append(ma_analysis)
            
            # Pequeno delay se não estiver usando queue manager
            if queue_manager is None:
                time.sleep(0.5)
        else:
            ma_signals.append("DADOS INSUFICIENTES")
            ma_strengths.append(0)
            ma_details.append({})
    
    progress_text.empty()
    
    # Preencher o restante com valores padrão
    for i in range(len(limited_df), len(df)):
        ma_signals.append("NÃO ANALISADO")
        ma_strengths.append(0)
        ma_details.append({})
    
    df['ma_signal'] = ma_signals
    df['ma_strength'] = ma_strengths
    df['ma_analysis'] = ma_details
    
    return df

def format_ma_analysis_for_display(ma_analysis: Dict) -> str:
    """
    Formata análise de MA para exibição na tabela
    
    Args:
        ma_analysis: Dict com análise de MA
    
    Returns:
        String formatada para display
    """
    if not ma_analysis or '4h' not in ma_analysis:
        return "Sem dados"
    
    tf_data = ma_analysis['4h']
    
    if not tf_data:
        return "Sem dados"
    
    # Símbolos
    touch_sma = "✓" if tf_data.get('touched_sma') else "○"
    touch_ema = "✓" if tf_data.get('touched_ema') else "○"
    trend = "↗" if tf_data.get('trend_sma') == 'ALTA' else "↘"
    
    # Tipo de toque
    touch_type = ""
    if tf_data.get('touch_type_sma') == "COMPRA":
        touch_type = "🟢"
    elif tf_data.get('touch_type_sma') == "VENDA":
        touch_type = "🔴"
    
    # Proximidade
    near_symbol = "🔍" if tf_data.get('near_sma') or tf_data.get('near_ema') else ""
    
    # Distâncias
    dist_sma = tf_data.get('distance_sma_pct', 0)
    
    # Inclinação
    slope = tf_data.get('sma_slope', 0)
    slope_emoji = "📈" if slope > 0.5 else "📉" if slope < -0.5 else "➡️"
    
    return f"SMA:{touch_sma} EMA:{touch_ema} {trend} {touch_type} {near_symbol} ({dist_sma:+.1f}%) {slope_emoji}"

def get_ma_statistics(df: pd.DataFrame) -> Dict:
    """
    Calcula estatísticas sobre análise de MA
    
    Args:
        df: DataFrame com análise de MA
    
    Returns:
        Dict com estatísticas
    """
    if 'ma_signal' not in df.columns:
        return {}
    
    analyzed = df[df['ma_signal'] != 'NÃO ANALISADO']
    
    if len(analyzed) == 0:
        return {}
    
    return {
        'total_analyzed': len(analyzed),
        'strong_buy': len(analyzed[analyzed['ma_signal'].str.contains('FORTE COMPRA', na=False)]),
        'buy': len(analyzed[analyzed['ma_signal'].str.contains('COMPRA', na=False)]) - len(analyzed[analyzed['ma_signal'].str.contains('FORTE COMPRA', na=False)]),
        'neutral': len(analyzed[analyzed['ma_signal'].str.contains('NEUTRO', na=False)]),
        'sell': len(analyzed[analyzed['ma_signal'].str.contains('VENDA', na=False)]) - len(analyzed[analyzed['ma_signal'].str.contains('FORTE VENDA', na=False)]),
        'strong_sell': len(analyzed[analyzed['ma_signal'].str.contains('FORTE VENDA', na=False)]),
        'avg_strength': analyzed['ma_strength'].mean(),
        'touched_count': len(analyzed[analyzed['ma_analysis'].apply(lambda x: x.get('4h', {}).get('touched_sma', False) or x.get('4h', {}).get('touched_ema', False))])
    }