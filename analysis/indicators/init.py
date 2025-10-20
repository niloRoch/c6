"""
Crypto Risk Analyzer Pro Elite V3
Análise avançada de risco cripto com sistema de fila inteligente
"""

__version__ = "3.0.0"
__author__ = "Crypto Analysis Team"
__description__ = "Sistema avançado de análise de risco cripto com indicadores técnicos, sistema de fila inteligente e visualizações em tempo real"

from .coingecko_api import get_top_coins, get_historical_data_optimized
from .risk_model import calculate_risk_score
from .leverage_model import calculate_leverage_suggestion
from .queue_manager import SmartRequestQueueManager, get_request_manager
from .advanced_indicators import AdvancedTechnicalIndicators, calculate_advanced_indicators