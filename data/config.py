"""
Configurações centralizadas do Crypto Risk Analyzer
Ajuste estes valores conforme necessário
"""

# ============================================================
# CONFIGURAÇÕES DA API COINGECKO
# ============================================================

# Rate Limiting
API_RATE_LIMIT = {
    'min_interval': 1.5,        # Segundos entre requisições
    'max_retries': 3,            # Número máximo de tentativas
    'retry_wait': 60,            # Segundos de espera após rate limit
    'progressive_wait': True     # Aumentar tempo de espera a cada retry
}

# Cache
API_CACHE = {
    'coins_list_ttl': 300,       # 5 minutos para lista de moedas
    'coin_history_ttl': 600,     # 10 minutos para histórico
    'indicators_ttl': 600        # 10 minutos para indicadores
}

# Limites de requisições
API_LIMITS = {
    'free_tier_limit': 50,       # Requisições por minuto (tier gratuito)
    'coins_per_page': 100,       # Moedas por página
    'max_pages': 1               # Número de páginas a buscar
}

# ============================================================
# CONFIGURAÇÕES DE ANÁLISE
# ============================================================

# Médias Móveis
MA_CONFIG = {
    'enabled': True,
    'timeframe': '4h',           # Apenas 4h para otimização
    'period': 200,               # Período da MA
    'max_coins': 15,             # Limitar análise às top N moedas
    'proximity_threshold': 2.0,  # % para considerar "próximo" da MA
    'analysis_candles': 3        # Número de candles para verificar toque
}

# Indicadores de Momentum
MOMENTUM_CONFIG = {
    'enabled': True,
    'rsi_period': 14,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'stochastic_period': 14,
    'stochastic_smooth': 3
}

# Indicadores de Volatilidade
VOLATILITY_CONFIG = {
    'enabled': True,
    'atr_period': 14,
    'bb_period': 20,
    'bb_std_dev': 2,
    'historical_vol_period': 30
}

# Volume Profile
VOLUME_CONFIG = {
    'enabled': False,            # Desabilitado por padrão
    'price_levels': 20,
    'value_area_volume': 0.7     # 70% do volume
}

# ============================================================
# CONFIGURAÇÕES DE RISCO
# ============================================================

RISK_CONFIG = {
    'volatility_weight': 0.4,    # 40% do score
    'liquidity_weight': 0.3,     # 30% do score
    'market_size_weight': 0.3,   # 30% do score
    'risk_levels': {
        'very_low': (0, 20),
        'low': (20, 40),
        'moderate': (40, 60),
        'high': (60, 80),
        'very_high': (80, 100)
    }
}

# Alavancagem
LEVERAGE_CONFIG = {
    'max_leverage': 10,
    'min_leverage': 1,
    'formula': lambda risk: max(1, 10 - (risk / 10))
}

# ============================================================
# CONFIGURAÇÕES DE INTERFACE
# ============================================================

# Dashboard
DASHBOARD_CONFIG = {
    'default_top_n': 50,
    'max_display_coins': 100,
    'auto_refresh': False,
    'refresh_interval': 5,       # Minutos
    'show_emojis': True
}

# Cores do tema
THEME_COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#3b82f6'
}

# Filtros padrão
DEFAULT_FILTERS = {
    'risk_range': (0, 100),
    'min_market_cap': 0,
    'min_volume': 0,
    'sort_by': 'Risco'
}

# ============================================================
# CONFIGURAÇÕES DE PERFORMANCE
# ============================================================

PERFORMANCE_CONFIG = {
    'enable_progress_bar': True,
    'enable_status_messages': True,
    'enable_warnings': True,
    'enable_info_messages': True,
    'parallel_processing': False  # Não implementado ainda
}

# ============================================================
# MENSAGENS E TEXTOS
# ============================================================

MESSAGES = {
    'loading': "📡 Carregando dados da CoinGecko...",
    'calculating_risk': "🧮 Calculando métricas de risco...",
    'calculating_ma': "📊 Analisando Médias Móveis (4h - Top {n})...",
    'calculating_momentum': "⚡ Calculando indicadores de Momentum...",
    'calculating_volatility': "📉 Calculando indicadores de Volatilidade...",
    'success': "✅ Dados carregados com sucesso!",
    'error_api': "❌ Erro ao carregar dados da API. Tente novamente em alguns minutos.",
    'rate_limit': "⏳ Rate limit atingido. Aguardando...",
    'no_data': "❌ Nenhum dado disponível após aplicar os filtros."
}

# Avisos
WARNINGS = {
    'rate_limit': """
    ⚠️ **Rate Limit da API CoinGecko**
    
    A API gratuita tem limite de 50 requisições/minuto.
    
    **Dicas para evitar bloqueio:**
    - Aguarde 1-2 minutos entre recarregamentos
    - Use auto-refresh com intervalo ≥ 5 minutos
    - Desative indicadores não essenciais
    - O sistema já tem cache e rate limiting automático
    """,
    
    'ma_limited': """
    ℹ️ **Análise MA Limitada**
    
    Para otimizar requisições à API, a análise de Médias Móveis
    está limitada às top 15 moedas por volume.
    """,
    
    'synthetic_data': """
    ℹ️ **Dados Sintéticos**
    
    Alguns indicadores (Momentum, Volatilidade) usam aproximações
    baseadas em dados de 24h disponíveis. Para análise precisa,
    use plataformas de trading profissionais.
    """
}

# ============================================================
# HELP TEXTS
# ============================================================

HELP_TEXTS = {
    'risk_score': """
    Score de 0-100 baseado em:
    - Volatilidade (40%)
    - Liquidez (30%)
    - Tamanho do mercado (30%)
    
    Menor score = Menor risco
    """,
    
    'leverage': """
    Alavancagem sugerida baseada no score de risco.
    Fórmula: max(1, 10 - (risco / 10))
    
    Sempre use stop loss!
    """,
    
    'ma_signal': """
    Analisa toque na MA 200 no gráfico de 4h.
    
    Sinais:
    - FORTE COMPRA: Tocou SMA por baixo
    - COMPRA: Tocou EMA por baixo
    - VENDA: Tocou por cima
    """,
    
    'rsi': """
    RSI (0-100):
    - < 30: Sobrevendido
    - > 70: Sobrecomprado
    - 45-55: Neutro
    """,
    
    'atr': """
    ATR%: Volatilidade como % do preço
    
    - < 2%: Baixa volatilidade
    - 2-5%: Moderada
    - > 5%: Alta volatilidade
    """
}

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def get_config(section: str, key: str = None):
    """
    Retorna configuração específica
    
    Args:
        section: Nome da seção (ex: 'API_RATE_LIMIT')
        key: Chave específica (opcional)
    """
    config_map = {
        'api_rate_limit': API_RATE_LIMIT,
        'api_cache': API_CACHE,
        'api_limits': API_LIMITS,
        'ma': MA_CONFIG,
        'momentum': MOMENTUM_CONFIG,
        'volatility': VOLATILITY_CONFIG,
        'volume': VOLUME_CONFIG,
        'risk': RISK_CONFIG,
        'leverage': LEVERAGE_CONFIG,
        'dashboard': DASHBOARD_CONFIG,
        'theme': THEME_COLORS,
        'filters': DEFAULT_FILTERS,
        'performance': PERFORMANCE_CONFIG
    }
    
    section_config = config_map.get(section.lower())
    
    if key:
        return section_config.get(key) if section_config else None
    return section_config

def update_config(section: str, key: str, value):
    """
    Atualiza configuração em runtime
    
    Args:
        section: Nome da seção
        key: Chave a atualizar
        value: Novo valor
    """
    config_map = {
        'api_rate_limit': API_RATE_LIMIT,
        'api_cache': API_CACHE,
        'ma': MA_CONFIG,
        'momentum': MOMENTUM_CONFIG,
        'volatility': VOLATILITY_CONFIG,
        'dashboard': DASHBOARD_CONFIG
    }
    
    section_config = config_map.get(section.lower())
    if section_config and key in section_config:
        section_config[key] = value
        return True
    return False

# ============================================================
# VALIDAÇÕES
# ============================================================

def validate_config():
    """
    Valida configurações ao iniciar
    """
    errors = []
    
    # Validar rate limit
    if API_RATE_LIMIT['min_interval'] < 0.5:
        errors.append("min_interval muito baixo (mínimo 0.5s)")
    
    # Validar MA config
    if MA_CONFIG['max_coins'] > 30:
        errors.append("max_coins muito alto (máximo recomendado: 30)")
    
    # Validar pesos de risco
    total_weight = (RISK_CONFIG['volatility_weight'] + 
                   RISK_CONFIG['liquidity_weight'] + 
                   RISK_CONFIG['market_size_weight'])
    if abs(total_weight - 1.0) > 0.01:
        errors.append(f"Pesos de risco não somam 1.0 (atual: {total_weight})")
    
    return errors

# Validar ao importar
_config_errors = validate_config()
if _config_errors:
    print("⚠️ Avisos de configuração:")
    for error in _config_errors:
        print(f"  - {error}")
