import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Tuple

class AdvancedTechnicalIndicators:
    """
    Indicadores técnicos avançados para análise cripto
    """
    
    @staticmethod
    def calculate_support_resistance(high: pd.Series, low: pd.Series, close: pd.Series, 
                                   period: int = 20) -> Dict:
        """
        Calcula níveis de suporte e resistência usando pivot points
        """
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        
        return {
            'pivot': pivot.iloc[-1],
            'resistance_1': r1.iloc[-1],
            'resistance_2': r2.iloc[-1],
            'support_1': s1.iloc[-1],
            'support_2': s2.iloc[-1]
        }
    
    @staticmethod
    def calculate_ichimoku_cloud(high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        """
        Calcula Ichimoku Cloud (mais complexo)
        """
        # Períodos padrão do Ichimoku
        tenkan_period = 9
        kijun_period = 26
        senkou_b_period = 52
        
        tenkan_sen = (high.rolling(tenkan_period).max() + 
                     low.rolling(tenkan_period).min()) / 2
        kijun_sen = (high.rolling(kijun_period).max() + 
                    low.rolling(kijun_period).min()) / 2
        senkou_span_a = (tenkan_sen + kijun_sen) / 2
        senkou_span_b = (high.rolling(senkou_b_period).max() + 
                        low.rolling(senkou_b_period).min()) / 2
        
        # Deslocar para frente
        senkou_span_a = senkou_span_a.shift(kijun_period)
        senkou_span_b = senkou_span_b.shift(kijun_period)
        
        return {
            'tenkan_sen': tenkan_sen.iloc[-1],
            'kijun_sen': kijun_sen.iloc[-1],
            'senkou_span_a': senkou_span_a.iloc[-1],
            'senkou_span_b': senkou_span_b.iloc[-1],
            'chikou_span': close.shift(-kijun_period).iloc[-1],
            'cloud_bullish': senkou_span_a.iloc[-1] > senkou_span_b.iloc[-1]
        }
    
    @staticmethod
    def calculate_fibonacci_retracement(high: float, low: float) -> Dict:
        """
        Calcula níveis de Fibonacci retracement
        """
        diff = high - low
        
        return {
            'level_0': high,
            'level_0.236': high - diff * 0.236,
            'level_0.382': high - diff * 0.382,
            'level_0.5': high - diff * 0.5,
            'level_0.618': high - diff * 0.618,
            'level_0.786': high - diff * 0.786,
            'level_1': low
        }
    
    @staticmethod
    def calculate_market_strength(volume: pd.Series, price_change: pd.Series) -> float:
        """
        Calcula força do mercado baseado em volume e mudança de preço
        """
        volume_trend = volume.pct_change().mean()
        price_momentum = price_change.mean()
        
        # Score combinado
        strength_score = (volume_trend * 0.6 + price_momentum * 0.4) * 100
        return max(0, min(100, strength_score + 50))
    
    @staticmethod
    def detect_divergence(price: pd.Series, indicator: pd.Series, window: int = 14) -> str:
        """
        Detecta divergência entre preço e indicador
        """
        if len(price) < window * 2:
            return "INSUFICIENT_DATA"
        
        price_highs = price.rolling(window).max()
        indicator_highs = indicator.rolling(window).max()
        
        price_lows = price.rolling(window).min()
        indicator_lows = indicator.rolling(window).min()
        
        # Verificar divergência de alta
        if (price_highs.iloc[-1] > price_highs.iloc[-2] and 
            indicator_highs.iloc[-1] < indicator_highs.iloc[-2]):
            return "BULLISH_DIVERGENCE"
        
        # Verificar divergência de baixa
        if (price_lows.iloc[-1] < price_lows.iloc[-2] and 
            indicator_lows.iloc[-1] > indicator_lows.iloc[-2]):
            return "BEARISH_DIVERGENCE"
        
        return "NO_DIVERGENCE"

def calculate_advanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica indicadores avançados ao DataFrame
    """
    df = df.copy()
    advanced = AdvancedTechnicalIndicators()
    
    support_resistance = []
    market_strength = []
    
    for idx, row in df.iterrows():
        try:
            # Criar dados sintéticos para demonstração
            prices = pd.Series([row['current_price'] * (1 + i * 0.01) 
                              for i in range(-10, 10)])
            highs = prices * 1.02
            lows = prices * 0.98
            
            # Calcular suporte/resistência
            sr_levels = advanced.calculate_support_resistance(highs, lows, prices)
            support_resistance.append(sr_levels)
            
            # Calcular força do mercado
            volume_data = pd.Series([row['total_volume']] * 20)
            price_changes = pd.Series([row['price_change_percentage_24h'] / 100] * 20)
            strength = advanced.calculate_market_strength(volume_data, price_changes)
            market_strength.append(strength)
            
        except Exception:
            support_resistance.append({})
            market_strength.append(50)
    
    df['support_resistance'] = support_resistance
    df['market_strength'] = market_strength
    
    return df