import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data.coingecko_api import get_top_coins, get_historical_data_optimized
from analysis.risk_model import calculate_risk_score
from analysis.leverage_model import calculate_leverage_suggestion
from analysis.indicators.volume_profile import volume_based_indicators, calculate_volume_spike
from analysis.indicators.ma_analysis import calculate_ma_indicators, format_ma_analysis_for_display
from analysis.indicators.momentum_indicators import calculate_momentum_indicators
from analysis.indicators.volatility_indicators import calculate_volatility_indicators
from analysis.advanced_indicators import calculate_advanced_indicators
from analysis.queue_manager import SmartRequestQueueManager, get_request_manager
import time
from datetime import datetime
import numpy as np

# Configuração da página ultra moderna
st.set_page_config(
    page_title="Crypto Risk Analyzer Pro Elite V3",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar gerenciador de fila inteligente
if 'queue_manager' not in st.session_state:
    st.session_state.queue_manager = get_request_manager()

# CSS customizado ultra moderno atualizado
st.markdown("""
<style>
    .main-header {
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 2rem 0;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.2);
        animation: gradient-shift 4s ease infinite;
        background-size: 300% 300%;
        margin-bottom: 1rem;
    }
    
    @keyframes gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .crypto-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .dashboard-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .dashboard-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
    }
    
    .signal-badge {
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: bold;
        font-size: 0.9rem;
        margin: 0.2rem;
        display: inline-block;
    }
    
    .strong-buy { background: linear-gradient(135deg, #00b09b, #96c93d); }
    .buy { background: linear-gradient(135deg, #11998e, #38ef7d); }
    .neutral { background: linear-gradient(135deg, #8e9eab, #eef2f3); }
    .sell { background: linear-gradient(135deg, #ff5e62, #ff9966); }
    .strong-sell { background: linear-gradient(135deg, #ff416c, #ff4b2b); }
    
    .volume-pulse {
        animation: volume-pulse 2s ease-in-out infinite;
    }
    
    @keyframes volume-pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.8; }
    }
    
    .ma-touch-glow {
        animation: ma-glow 3s ease-in-out infinite;
        box-shadow: 0 0 20px rgba(255, 193, 7, 0.5);
    }
    
    @keyframes ma-glow {
        0%, 100% { box-shadow: 0 0 20px rgba(255, 193, 7, 0.5); }
        50% { box-shadow: 0 0 30px rgba(255, 193, 7, 0.8); }
    }
</style>
""", unsafe_allow_html=True)

def create_advanced_gauge_chart(value, title, max_value=100, thresholds=None):
    """Cria gráfico de gauge avançado com múltiplas zonas"""
    if thresholds is None:
        thresholds = [max_value/3, 2*max_value/3]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta+advanced",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 24, 'color': '#2c3e50', 'family': 'Arial Black'}},
        delta={'reference': max_value/2, 'increasing': {'color': '#11998e'}, 'decreasing': {'color': '#ee0979'}},
        gauge={
            'axis': {'range': [None, max_value], 'tickwidth': 2, 'tickcolor': "#34495e"},
            'bar': {'color': "#667eea", 'thickness': 0.85},
            'bgcolor': "white",
            'borderwidth': 3,
            'bordercolor': "#34495e",
            'steps': [
                {'range': [0, thresholds[0]], 'color': 'rgba(46, 204, 113, 0.6)'},
                {'range': [thresholds[0], thresholds[1]], 'color': 'rgba(243, 156, 18, 0.6)'},
                {'range': [thresholds[1], max_value], 'color': 'rgba(231, 76, 60, 0.6)'}
            ],
            'threshold': {
                'line': {'color': "#c0392b", 'width': 6},
                'thickness': 0.9,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        height=300, 
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Arial, sans-serif'}
    )
    return fig

def generate_advanced_trading_signal(row):
    """Gera sinal de trading ultra avançado com múltiplos fatores"""
    score = 0
    signals = []
    weights = {
        'risk': 0.15,
        'ma': 0.25,
        'rsi': 0.20,
        'macd': 0.15,
        'volume': 0.15,
        'volatility': 0.10
    }
    
    # Score baseado em risco (invertido)
    risk_score = row.get('risk_score', 50)
    risk_component = max(0, 100 - risk_score) * weights['risk']
    score += risk_component
    
    if risk_score < 25:
        signals.append("🎯 Risco Muito Baixo")
    elif risk_score < 40:
        signals.append("✅ Risco Baixo")
    elif risk_score > 75:
        signals.append("🚨 Risco Muito Alto")
    elif risk_score > 60:
        signals.append("⚠️ Risco Alto")
    
    # Score baseado em MA
    if 'ma_signal' in row and pd.notna(row['ma_signal']):
        ma_signal = str(row['ma_signal'])
        if 'FORTE COMPRA' in ma_signal:
            score += 100 * weights['ma']
            signals.append("📈 MA: Forte Compra")
        elif 'COMPRA' in ma_signal:
            score += 75 * weights['ma']
            signals.append("📈 MA: Compra")
        elif 'FORTE VENDA' in ma_signal:
            score += 0 * weights['ma']
            signals.append("📉 MA: Forte Venda")
        elif 'VENDA' in ma_signal:
            score += 25 * weights['ma']
            signals.append("📉 MA: Venda")
    
    # Score baseado em RSI
    if 'rsi' in row and pd.notna(row['rsi']):
        rsi = row['rsi']
        if rsi < 25:
            score += 100 * weights['rsi']
            signals.append("🔥 RSI Extrema Sobrevenda")
        elif rsi < 35:
            score += 80 * weights['rsi']
            signals.append("📉 RSI Sobrevenda")
        elif rsi > 75:
            score += 0 * weights['rsi']
            signals.append("🎯 RSI Extrema Sobrecompra")
        elif rsi > 65:
            score += 20 * weights['rsi']
            signals.append("📈 RSI Sobrecompra")
        else:
            score += 50 * weights['rsi']
    
    # Score baseado em MACD
    if 'macd_signal' in row and pd.notna(row['macd_signal']):
        if row['macd_signal'] == 'COMPRA':
            score += 80 * weights['macd']
            signals.append("📊 MACD Compra")
        elif row['macd_signal'] == 'VENDA':
            score += 20 * weights['macd']
            signals.append("📊 MACD Venda")
    
    # Score baseado em volume
    if 'volume_spike' in row and pd.notna(row['volume_spike']):
        if row['volume_spike'] > 2.0:
            score += 90 * weights['volume']
            signals.append("🚀 Volume Spike 2x+")
        elif row['volume_spike'] > 1.5:
            score += 70 * weights['volume']
            signals.append("📈 Volume Aumentou 50%+")
    
    # Score baseado em volatilidade
    if 'atr_pct' in row and pd.notna(row['atr_pct']):
        if row['atr_pct'] < 2:
            score += 80 * weights['volatility']
            signals.append("⚡ Baixa Volatilidade")
        elif row['atr_pct'] > 10:
            score += 20 * weights['volatility']
            signals.append("🌪️ Volatilidade Extrema")
        elif row['atr_pct'] > 6:
            score += 40 * weights['volatility']
            signals.append("💨 Alta Volatilidade")
    
    # Bônus por MA touch
    if row.get('ma_touched', False):
        score += 15
        signals.append(f"🎯 {row.get('ma_touch_details', 'MA Touch')}")
    
    # Determinar sinal final
    if score >= 80:
        signal = "🚀 FORTE COMPRA"
        color = "strong-buy"
        confidence = "MUITO ALTA"
    elif score >= 65:
        signal = "🟢 COMPRA"
        color = "buy"
        confidence = "ALTA"
    elif score >= 45:
        signal = "⚪ NEUTRO"
        color = "neutral"
        confidence = "MÉDIA"
    elif score >= 30:
        signal = "🔴 VENDA"
        color = "sell"
        confidence = "ALTA"
    else:
        signal = "🚨 FORTE VENDA"
        color = "strong-sell"
        confidence = "MUITO ALTA"
    
    return {
        'signal': signal,
        'score': int(score),
        'color': color,
        'confidence': confidence,
        'reasons': signals,
        'components': {
            'risk': risk_component,
            'ma': score * weights['ma'],
            'rsi': score * weights['rsi'],
            'macd': score * weights['macd'],
            'volume': score * weights['volume'],
            'volatility': score * weights['volatility']
        }
    }

def create_volume_analysis_tab():
    """Cria aba dedicada para análise de volume"""
    st.markdown("## 🔥 Análise de Volume em Tempo Real")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Volume Total Analisado", 
                 f"${df['total_volume'].sum()/1e9:.2f}B")
    
    with col2:
        spike_coins = len(df[df['volume_spike'] > 1.5])
        st.metric("🚀 Spikes de Volume", spike_coins)
    
    with col3:
        avg_spike = df['volume_spike'].mean()
        st.metric("📈 Spike Médio", f"{avg_spike:.2f}x")
    
    # Top volume spikes
    st.markdown("### 🚀 Maiores Aumentos de Volume")
    volume_spikes = df.nlargest(10, 'volume_spike')[['name', 'volume_spike', 
                                                    'total_volume', 'current_price',
                                                    'price_change_percentage_24h']]
    
    for _, coin in volume_spikes.iterrows():
        with st.container():
            cols = st.columns([3, 2, 2, 2])
            with cols[0]:
                st.markdown(f"**{coin['name']}**")
                st.caption(f"Volume: ${coin['total_volume']/1e6:.2f}M")
            with cols[1]:
                st.markdown(f"<div class='volume-pulse' style='background: linear-gradient(135deg, #ffa751 0%, #ffe259 100%); padding: 0.5rem; border-radius: 10px; color: #333; text-align: center; font-weight: bold;'>🔥 {coin['volume_spike']:.2f}x</div>", unsafe_allow_html=True)
            with cols[2]:
                st.metric("Preço", f"${coin['current_price']:.2f}")
            with cols[3]:
                st.metric("24h", f"{coin['price_change_percentage_24h']:+.2f}%")
    
    # Gráfico de volume spikes
    fig = px.bar(volume_spikes, x='name', y='volume_spike',
                 title="Top 10 Volume Spikes",
                 color='volume_spike',
                 color_continuous_scale='Oranges')
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

def create_oversold_overbought_tab():
    """Cria aba dedicada para ativos sobrevendidos/sobrecomprados"""
    st.markdown("## 📊 Análise de Momentum Extremo")
    
    # Dados sobrevendidos e sobrecomprados
    oversold = df[df['rsi'] < 30] if 'rsi' in df.columns else pd.DataFrame()
    overbought = df[df['rsi'] > 70] if 'rsi' in df.columns else pd.DataFrame()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📉 Ativos Sobrevendidos (RSI < 30)")
        if not oversold.empty:
            for _, coin in oversold.nsmallest(5, 'rsi').iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; margin: 0.5rem 0;'>
                        <h4 style='margin: 0; color: white;'>{coin['name']}</h4>
                        <p style='margin: 0.2rem 0; color: white;'>RSI: <strong>{coin['rsi']:.1f}</strong></p>
                        <p style='margin: 0.2rem 0; color: white;'>Preço: ${coin['current_price']:.2f}</p>
                        <p style='margin: 0; color: white;'>24h: {coin['price_change_percentage_24h']:+.2f}%</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Nenhum ativo sobrevendido no momento")
    
    with col2:
        st.markdown("### 📈 Ativos Sobrecomprados (RSI > 70)")
        if not overbought.empty:
            for _, coin in overbought.nlargest(5, 'rsi').iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #ff6b6b 0%, #ffa8a8 100%); padding: 1rem; border-radius: 10px; margin: 0.5rem 0;'>
                        <h4 style='margin: 0; color: white;'>{coin['name']}</h4>
                        <p style='margin: 0.2rem 0; color: white;'>RSI: <strong>{coin['rsi']:.1f}</strong></p>
                        <p style='margin: 0.2rem 0; color: white;'>Preço: ${coin['current_price']:.2f}</p>
                        <p style='margin: 0; color: white;'>24h: {coin['price_change_percentage_24h']:+.2f}%</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Nenhum ativo sobrecomprado no momento")
    
    # Gráfico RSI geral
    if 'rsi' in df.columns:
        fig = px.scatter(df, x='current_price', y='rsi', 
                        size='total_volume', color='rsi',
                        hover_data=['name', 'price_change_percentage_24h'],
                        title="RSI vs Preço - Todos os Ativos",
                        color_continuous_scale='RdYlGn_r')
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Sobrecomprado")
        fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Sobrevendido")
        st.plotly_chart(fig, use_container_width=True)

def create_ma_analysis_tab():
    """Cria aba dedicada para análise de Médias Móveis"""
    st.markdown("## 📊 Análise de Médias Móveis - Últimas 4 Horas")
    
    # Filtrar ativos que tocaram MA de 200 períodos
    ma_touch_coins = df[df['ma_touched'] == True] if 'ma_touched' in df.columns else pd.DataFrame()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("🎯 Ativos com MA Touch", len(ma_touch_coins))
    
    with col2:
        if not ma_touch_coins.empty:
            avg_distance = ma_touch_coins['ma_distance_pct'].abs().mean()
            st.metric("📏 Distância Média", f"{avg_distance:.2f}%")
    
    # Lista de ativos com MA touch
    st.markdown("### 🎯 Ativos que Tocaram MA de 200 Períodos")
    if not ma_touch_coins.empty:
        for _, coin in ma_touch_coins.iterrows():
            with st.container():
                cols = st.columns([3, 2, 2, 2])
                with cols[0]:
                    st.markdown(f"**{coin['name']}**")
                    st.caption(f"Detalhes: {coin.get('ma_touch_details', 'N/A')}")
                with cols[1]:
                    distance = coin.get('ma_distance_pct', 0)
                    color = "green" if distance > 0 else "red"
                    st.markdown(f"<div style='color: {color}; font-weight: bold;'>Distância: {distance:+.2f}%</div>", unsafe_allow_html=True)
                with cols[2]:
                    st.metric("Preço", f"${coin['current_price']:.2f}")
                with cols[3]:
                    st.metric("24h", f"{coin['price_change_percentage_24h']:+.2f}%")
    else:
        st.info("Nenhum ativo tocou a MA de 200 períodos nas últimas 4 horas")

def main():
    # Header ultra moderno
    st.markdown('<h1 class="main-header">🚀 CRYPTO RISK ANALYZER PRO ELITE V3</h1>', unsafe_allow_html=True)
    
    # Status do sistema
    queue_status = st.session_state.queue_manager.get_status()
    
    # Sidebar avançada
    with st.sidebar:
        st.markdown("## ⚙️ Controles Avançados")
        
        # Configurações de atualização
        st.markdown("### 🔄 Auto-Atualização")
        auto_refresh = st.checkbox("Atualização Automática", value=True)
        refresh_interval = st.slider("Intervalo (minutos)", 1, 15, 5)
        
        # Filtros
        st.markdown("### 🔍 Filtros")
        min_volume = st.number_input("Volume Mínimo (USD)", value=1000000, step=1000000)
        risk_filter = st.slider("Risco Máximo", 0, 100, 80)
        
        # Status do sistema
        st.markdown("### 📊 Status do Sistema")
        st.metric("Fila Ativa", queue_status['total_pending'])
        st.metric("Cache Hit Rate", f"{queue_status['efficiency']:.1f}%")
        st.metric("Tempo Médio Resp", f"{queue_status['avg_response_time']:.2f}s")
    
    # Carregar dados com sistema de fila
    with st.spinner("🔄 Carregando dados via fila inteligente..."):
        df = get_top_coins()
        
        if df.empty:
            st.error("❌ Erro ao carregar dados. Verifique a conexão.")
            return
        
        # Aplicar filtros
        df = df[df['total_volume'] >= min_volume]
        
        # Calcular indicadores
        df = calculate_risk_score(df)
        df = calculate_leverage_suggestion(df)
        df = volume_based_indicators(df)
        df = calculate_ma_indicators(df)
        df = calculate_momentum_indicators(df)
        df = calculate_volatility_indicators(df)
        df = calculate_advanced_indicators(df)
        
        # Gerar sinais de trading
        trading_signals = []
        for _, row in df.iterrows():
            signal = generate_advanced_trading_signal(row)
            trading_signals.append(signal)
        
        df['trading_signal'] = [s['signal'] for s in trading_signals]
        df['signal_score'] = [s['score'] for s in trading_signals]
        df['signal_color'] = [s['color'] for s in trading_signals]
        df['signal_confidence'] = [s['confidence'] for s in trading_signals]
        df['signal_reasons'] = [s['reasons'] for s in trading_signals]
    
    # Dashboard principal
    st.markdown("## 📊 Dashboard Principal - Análise em Tempo Real")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Total de Ativos", len(df))
    with col2:
        avg_risk = df['risk_score'].mean()
        st.metric("⚡ Risco Médio", f"{avg_risk:.1f}")
    with col3:
        strong_buy = len(df[df['trading_signal'] == "🚀 FORTE COMPRA"])
        st.metric("🚀 Fortes Compras", strong_buy)
    with col4:
        volume_24h = df['total_volume'].sum() / 1e9
        st.metric("📈 Volume 24h", f"${volume_24h:.2f}B")
    
    # Abas principais
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Sinais de Trading", 
        "📊 Volume", 
        "📈 Momentum", 
        "📏 Médias Móveis",
        "📋 Tabela Completa"
    ])
    
    with tab1:
        # Exibir sinais de trading
        st.markdown("## 🎯 Sinais de Trading Avançados")
        
        # Ordenar por score
        df_sorted = df.sort_values('signal_score', ascending=False)
        
        for _, coin in df_sorted.iterrows():
            signal_info = generate_advanced_trading_signal(coin)
            
            with st.container():
                st.markdown(f"""
                <div class='dashboard-card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <h3 style='margin: 0;'>{coin['name']} ({coin['symbol'].upper()})</h3>
                            <p style='margin: 0.2rem 0; color: #666;'>Rank: #{coin.get('market_cap_rank', 'N/A')} | Volume: ${coin['total_volume']/1e6:.2f}M</p>
                        </div>
                        <div style='text-align: right;'>
                            <span class='signal-badge {signal_info["color"]}'>{signal_info['signal']}</span>
                            <p style='margin: 0.2rem 0; font-size: 0.9rem;'>Confiança: {signal_info['confidence']}</p>
                            <p style='margin: 0; font-size: 1.2rem; font-weight: bold;'>Score: {signal_info['score']}/100</p>
                        </div>
                    </div>
                    
                    <div style='margin-top: 1rem;'>
                        <div style='display: flex; gap: 1rem; margin-bottom: 0.5rem;'>
                            <div><strong>Preço:</strong> ${coin['current_price']:.4f}</div>
                            <div><strong>24h:</strong> <span style='color: {"#00b09b" if coin["price_change_percentage_24h"] > 0 else "#ff416c"}'>
                                {coin["price_change_percentage_24h"]:+.2f}%</span></div>
                            <div><strong>RSI:</strong> {coin.get('rsi', 'N/A'):.1f}</div>
                            <div><strong>Volume Spike:</strong> {coin.get('volume_spike', 1):.2f}x</div>
                        </div>
                        
                        <div style='margin-top: 0.5rem;'>
                            <strong>Razões:</strong> {' • '.join(signal_info['reasons'][:3])}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        create_volume_analysis_tab()
    
    with tab3:
        create_oversold_overbought_tab()
    
    with tab4:
        create_ma_analysis_tab()
    
    with tab5:
        # Tabela completa
        st.markdown("## 📋 Dados Completos dos Ativos")
        
        # Colunas para exibir
        display_columns = ['name', 'current_price', 'price_change_percentage_24h', 
                          'total_volume', 'risk_score', 'rsi', 'volume_spike',
                          'trading_signal', 'signal_score']
        
        display_df = df[display_columns].copy()
        st.dataframe(display_df, use_container_width=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval * 60)
        st.rerun()

if __name__ == "__main__":
    main()