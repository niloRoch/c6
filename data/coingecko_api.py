import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import time
from queue_manager import get_request_manager

@st.cache_data(ttl=300)
def get_top_coins_via_queue():
    """
    Obtém top coins usando sistema de fila
    """
    queue_manager = get_request_manager()
    
    def fetch_coins():
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'volume_desc',
            'per_page': 100,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h,7d,30d'
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    
    # Usar fila com alta prioridade
    result = queue_manager.execute_with_retry(
        fetch_coins, 
        'top_coins_100', 
        max_retries=3
    )
    
    if result and isinstance(result, list):
        df = pd.DataFrame(result)
        
        # Renomear colunas
        df = df.rename(columns={
            'id': 'coin_id',
            'symbol': 'symbol', 
            'name': 'name',
            'current_price': 'current_price',
            'market_cap': 'market_cap',
            'market_cap_rank': 'market_cap_rank',
            'total_volume': 'total_volume',
            'high_24h': 'high_24h',
            'low_24h': 'low_24h',
            'price_change_24h': 'price_change_24h',
            'price_change_percentage_24h': 'price_change_percentage_24h',
            'price_change_percentage_7d': 'price_change_percentage_7d',
            'price_change_percentage_30d': 'price_change_percentage_30d',
            'circulating_supply': 'circulating_supply',
            'total_supply': 'total_supply',
            'ath': 'ath',
            'ath_change_percentage': 'ath_change_percentage',
            'last_updated': 'last_updated'
        })
        
        if 'id' not in df.columns:
            df['id'] = df['coin_id']
            
        return df
    
    return pd.DataFrame()

def get_historical_data_optimized(coin_id, days=30, queue_manager=None):
    """
    Obtém dados históricos usando sistema de fila
    """
    if queue_manager is None:
        queue_manager = get_request_manager()
    
    cache_key = f"historical_{coin_id}_{days}"
    
    def fetch_historical():
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'hourly' if days <= 7 else 'daily'
        }
        
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    
    data = queue_manager.execute_with_retry(
        fetch_historical, cache_key, max_retries=2
    )
    
    if data and 'prices' in data:
        prices = data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    
    return pd.DataFrame()

# Manter função original para compatibilidade
def get_top_coins(max_retries=3):
    return get_top_coins_via_queue()