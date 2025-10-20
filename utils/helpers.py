import pandas as pd
import streamlit as st

def format_currency(value):
    """
    Formata valores monetários de forma legível
    """
    if value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.2f}M"
    elif value >= 1e3:
        return f"${value/1e3:.2f}K"
    else:
        return f"${value:.2f}"

def format_percentage(value):
    """
    Formata porcentagens
    """
    return f"{value:.2f}%"

def validate_dataframe(df):
    """
    Valida se o DataFrame tem as colunas necessárias
    """
    required_columns = [
        'name', 'current_price', 'price_change_percentage_24h',
        'total_volume', 'market_cap'
    ]
    
    if df is None or df.empty:
        return False
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"Colunas faltando: {missing_columns}")
        return False
    
    return True

def get_risk_color(risk_score):
    """
    Retorna cor baseada no score de risco
    """
    if risk_score <= 30:
        return "🟢"  # Baixo risco
    elif risk_score <= 70:
        return "🟡"  # Risco médio
    else:
        return "🔴"  # Alto risco