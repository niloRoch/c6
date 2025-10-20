import time
import threading
from collections import deque, defaultdict
from datetime import datetime, timedelta
import asyncio
import pandas as pd

class SmartRequestQueueManager:
    """
    Gerenciador de fila inteligente com prioridades e cache distribuído
    """
    
    def __init__(self, max_requests_per_minute=45, request_interval=1.5):
        self.max_requests_per_minute = max_requests_per_minute
        self.request_interval = request_interval
        
        # Filas por prioridade
        self.queues = {
            'high': deque(),
            'normal': deque(),
            'low': deque()
        }
        
        # Cache multi-nível
        self.cache = {}
        self.cache_ttl = {}
        self.persistent_cache = {}
        
        # Estatísticas avançadas
        self.stats = {
            'total_requests': 0,
            'completed_requests': 0,
            'cached_responses': 0,
            'failed_requests': 0,
            'rate_limit_hits': 0,
            'avg_response_time': 0,
            'queue_times': deque(maxlen=100)
        }
        
        self.request_history = deque(maxlen=max_requests_per_minute)
        self.lock = threading.Lock()
        self.last_optimization = time.time()
        
    def add_request(self, request_id, request_func, priority='normal', 
                   cache_key=None, ttl=300, *args, **kwargs):
        """
        Adiciona requisição à fila com prioridade
        """
        request_data = {
            'id': request_id,
            'func': request_func,
            'args': args,
            'kwargs': kwargs,
            'priority': priority,
            'cache_key': cache_key,
            'ttl': ttl,
            'timestamp': time.time(),
            'status': 'pending',
            'attempts': 0
        }
        
        with self.lock:
            self.queues[priority].append(request_data)
            self.stats['total_requests'] += 1
            
        return request_id
    
    def process_batch(self, batch_size=10, timeout=30):
        """
        Processa um lote de requisições de forma otimizada
        """
        start_time = time.time()
        processed = 0
        results = {}
        
        while processed < batch_size and time.time() - start_time < timeout:
            # Obter próxima requisição por prioridade
            request = self._get_next_request()
            if not request:
                break
                
            try:
                # Verificar cache primeiro
                if request['cache_key']:
                    cached = self.get_from_cache(request['cache_key'])
                    if cached is not None:
                        results[request['id']] = cached
                        request['status'] = 'cached'
                        processed += 1
                        continue
                
                # Verificar rate limit
                if not self._can_make_request():
                    wait_time = self._calculate_wait_time()
                    time.sleep(wait_time)
                
                # Executar requisição
                request_start = time.time()
                result = request['func'](*request['args'], **request['kwargs'])
                request_time = time.time() - request_start
                
                # Atualizar estatísticas
                self.stats['queue_times'].append(request_time)
                self.stats['avg_response_time'] = (
                    sum(self.stats['queue_times']) / len(self.stats['queue_times'])
                )
                
                # Cachear resultado
                if request['cache_key']:
                    self.set_cache(request['cache_key'], result, request['ttl'])
                
                results[request['id']] = result
                request['status'] = 'completed'
                self.stats['completed_requests'] += 1
                processed += 1
                
                # Registrar requisição
                self.request_history.append(time.time())
                
            except Exception as e:
                request['status'] = 'failed'
                request['attempts'] += 1
                self.stats['failed_requests'] += 1
                
                # Reagendar se tiver tentativas restantes
                if request['attempts'] < 3:
                    self.queues['low'].appendleft(request)
                
                results[request['id']] = {'error': str(e)}
        
        return {
            'results': results,
            'processed': processed,
            'remaining': self.get_queue_size()
        }
    
    def _get_next_request(self):
        """Obtém próxima requisição por prioridade"""
        with self.lock:
            for priority in ['high', 'normal', 'low']:
                if self.queues[priority]:
                    return self.queues[priority].popleft()
        return None
    
    def _can_make_request(self):
        """Verifica se pode fazer nova requisição"""
        current_time = time.time()
        
        # Limpar histórico antigo
        while (self.request_history and 
               current_time - self.request_history[0] > 60):
            self.request_history.popleft()
        
        return len(self.request_history) < self.max_requests_per_minute
    
    def _calculate_wait_time(self):
        """Calcula tempo de espera otimizado"""
        if not self.request_history:
            return 0
        
        current_time = time.time()
        oldest_request = self.request_history[0]
        
        time_until_reset = 60 - (current_time - oldest_request)
        return max(0, time_until_reset + 0.1)
    
    def get_from_cache(self, cache_key):
        """Obtém do cache com TTL"""
        if cache_key in self.cache:
            cache_time = self.cache_ttl.get(cache_key, 0)
            if time.time() - cache_time < self.cache_ttl.get(f"{cache_key}_ttl", 300):
                self.stats['cached_responses'] += 1
                return self.cache[cache_key]
            else:
                del self.cache[cache_key]
                del self.cache_ttl[cache_key]
                del self.cache_ttl[f"{cache_key}_ttl"]
        
        return None
    
    def set_cache(self, cache_key, value, ttl=300):
        """Armazena no cache com TTL"""
        self.cache[cache_key] = value
        self.cache_ttl[cache_key] = time.time()
        self.cache_ttl[f"{cache_key}_ttl"] = ttl
    
    def get_queue_size(self):
        """Retorna tamanho total da fila"""
        return sum(len(queue) for queue in self.queues.values())
    
    def get_status(self):
        """Status detalhado do gerenciador"""
        current_time = time.time()
        
        # Limpar histórico
        while (self.request_history and 
               current_time - self.request_history[0] > 60):
            self.request_history.popleft()
        
        queue_sizes = {priority: len(queue) for priority, queue in self.queues.items()}
        
        return {
            'queues': queue_sizes,
            'total_pending': self.get_queue_size(),
            'completed': self.stats['completed_requests'],
            'failed': self.stats['failed_requests'],
            'cached': self.stats['cached_responses'],
            'rate_limit_hits': self.stats['rate_limit_hits'],
            'requests_last_minute': len(self.request_history),
            'cache_size': len(self.cache),
            'avg_response_time': self.stats['avg_response_time'],
            'efficiency': (self.stats['cached_responses'] / 
                          max(1, self.stats['total_requests'])) * 100
        }
    
    def optimize_queues(self):
        """Otimiza as filas removendo duplicatas"""
        with self.lock:
            for priority in self.queues:
                unique_requests = {}
                for request in self.queues[priority]:
                    request_key = f"{request['id']}_{request.get('cache_key', '')}"
                    unique_requests[request_key] = request
                
                self.queues[priority] = deque(unique_requests.values())
    
    def auto_adjust_rates(self):
        """Ajusta automaticamente as taxas baseado no desempenho"""
        stats = self.get_status()
        
        if stats['rate_limit_hits'] > 5:
            # Diminuir taxa
            self.request_interval = min(3.0, self.request_interval * 1.2)
        elif stats['rate_limit_hits'] == 0 and stats['completed'] > 20:
            # Aumentar taxa cuidadosamente
            self.request_interval = max(1.0, self.request_interval * 0.95)

# Singleton global para o gerenciador de fila
_request_manager = None

def get_request_manager():
    """Retorna instância única do gerenciador de requisições"""
    global _request_manager
    if _request_manager is None:
        _request_manager = SmartRequestQueueManager()
    return _request_manager