import asyncio
import json
import time
import logging
import os
from datetime import datetime

logger = logging.getLogger('robo_trader')

class PairMonitor:
    def __init__(self, iq_bot):
        self.iq_bot = iq_bot
        self.available_pairs = {}
        self.last_update = None
        self.monitoring = False
        self.best_opportunity = None
        self.monitoring_task = None
        self.update_interval = 30  # segundos entre atualizações (reduzido para 30s)
        
    async def start_monitoring(self):
        """Inicia o monitoramento contínuo de pares disponíveis"""
        if self.monitoring:
            return
            
        self.monitoring = True
        logger.info("Iniciando monitoramento de pares disponíveis...")
        
        # Forçar atualização imediata
        await self.update_available_pairs()
        
        # Iniciar o monitoramento em background
        self.monitoring_task = asyncio.create_task(self._monitor_pairs())
        logger.info("Monitoramento de pares iniciado")
        
    async def stop_monitoring(self):
        """Para o monitoramento de pares"""
        self.monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoramento de pares parado")
            
    async def _monitor_pairs(self):
        """Função de monitoramento que executa em background"""
        while self.monitoring:
            try:
                await self.update_available_pairs()
                if self.monitoring:  # verifica novamente porque pode ter mudado durante a execução
                    await self._analyze_opportunities()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no monitoramento de pares: {str(e)}")
                await asyncio.sleep(5)  # espera menos tempo antes de tentar novamente
                
    async def _analyze_opportunities(self):
        """Analisa os pares disponíveis buscando oportunidades"""
        # Implementação básica
        logger.debug(f"Analisando oportunidades entre {len(self.available_pairs)} pares disponíveis")
        
    async def update_available_pairs(self):
        """Atualiza a lista de pares disponíveis"""
        if not self.iq_bot or not hasattr(self.iq_bot, 'api'):
            logger.warning("IQ Bot não inicializado para verificar pares")
            return []
            
        try:
            logger.info("Solicitando lista de pares disponíveis da API...")
            all_pairs = self.iq_bot.api.get_all_open_time()
            
            # Debug: Salvar a resposta completa para análise
            debug_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'pairs_debug.json')
            os.makedirs(os.path.dirname(debug_file), exist_ok=True)
            with open(debug_file, 'w') as f:
                json.dump(all_pairs, f, indent=2)
            
            if not all_pairs:
                logger.warning("API retornou dados vazios para pares disponíveis")
                return []
            
            # Detectar todos os tipos de mercado disponíveis
            available = {}
            market_types = all_pairs.keys()  # Usar todas as chaves retornadas pela API
            
            # Processar cada tipo de mercado
            for market_type in market_types:
                logger.info(f"Processando mercado: {market_type}")
                    
                # Digital precisa de tratamento especial
                if market_type == "digital":
                    # Tratamento especial para opções digitais
                    try:
                        digital_pairs = self._get_digital_pairs()
                        for pair in digital_pairs:
                            pair_key = f"DIGITAL_{pair}"
                            available[pair_key] = {
                                "open": True,
                                "type": "digital",
                                "timestamp": time.time()
                            }
                        logger.info(f"Adicionados {len(digital_pairs)} pares digitais")
                    except Exception as e:
                        logger.error(f"Erro ao obter pares digitais: {str(e)}")
                else:
                    # Processamento para os outros mercados (binary, turbo, etc)
                    for pair_name, pair_status in all_pairs[market_type].items():
                        # Verificar se é um dicionário com chave "open"
                        if isinstance(pair_status, dict) and "open" in pair_status:
                            if pair_status["open"]:
                                pair_key = f"{market_type.upper()}_{pair_name}" if market_type != "binary" else pair_name
                                available[pair_key] = {
                                    "open": True,
                                    "type": market_type,
                                    "timestamp": time.time()
                                }
                        # Algumas versões da API retornam apenas um booleano
                        elif isinstance(pair_status, bool) and pair_status:
                            pair_key = f"{market_type.upper()}_{pair_name}" if market_type != "binary" else pair_name
                            available[pair_key] = {
                                "open": True,
                                "type": market_type,
                                "timestamp": time.time()
                            }
            
            # Verificar outros mercados alternativos usando consulta direta
            try:
                # Obter informações de lucro para detectar mais pares disponíveis
                profit_data = self.iq_bot.api.get_all_profit()
                if isinstance(profit_data, dict):
                    for asset_id, info in profit_data.items():
                        if isinstance(info, dict) and "name" in info:
                            asset_name = info["name"]
                            if asset_name not in available:
                                # Verificar se este ativo está disponível nos mercados conhecidos
                                for market_type in ["binary", "turbo"]:
                                    if market_type in all_pairs and asset_name in all_pairs[market_type]:
                                        status = all_pairs[market_type][asset_name]
                                        is_open = status.get("open", False) if isinstance(status, dict) else status
                                        if is_open:
                                            available[asset_name] = {
                                                "open": True,
                                                "type": market_type,
                                                "timestamp": time.time()
                                            }
                                            break
            except Exception as e:
                logger.error(f"Erro ao obter dados adicionais de pares: {str(e)}")
            
            # Verificar se temos algum par disponível
            if not available:
                logger.warning("Nenhum par disponível encontrado em nenhum mercado")
                    
                # Tente recuperar opções digitais como fallback
                try:
                    digital_pairs = self._get_digital_pairs()
                    for pair in digital_pairs:
                        pair_key = f"DIGITAL_{pair}"
                        available[pair_key] = {
                            "open": True,
                            "type": "digital", 
                            "timestamp": time.time()
                        }
                except Exception as e:
                    logger.error(f"Erro ao obter pares digitais fallback: {str(e)}")
            
            self.available_pairs = available
            self.last_update = datetime.now()
            
            # Salva em arquivo para consulta
            self._save_pairs_to_file()
            
            logger.info(f"Lista de pares atualizada. {len(available)} pares disponíveis.")
            return list(available.keys())
            
        except Exception as e:
            logger.error(f"Erro ao atualizar pares disponíveis: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _get_digital_pairs(self):
        """Obtém a lista de pares disponíveis para opções digitais"""
        if not self.iq_bot or not hasattr(self.iq_bot, 'api'):
            return []
        
        try:
            # Usar o método específico para opções digitais quando disponível
            if hasattr(self.iq_bot.api, 'get_digital_underlying'):
                return self.iq_bot.api.get_digital_underlying()
            else:
                logger.warning("Método get_digital_underlying não disponível na API")
                return []
        except Exception as e:
            logger.error(f"Erro ao obter pares digitais: {str(e)}")
            return []
    
    def _save_pairs_to_file(self):
        """Salva a lista de pares em um arquivo para consulta pelo frontend"""
        try:
            # Organizar pares por tipo de mercado para interface mais clara
            organized_pairs = {}
            for pair, data in self.available_pairs.items():
                market_type = data.get("type", "unknown")
                if market_type not in organized_pairs:
                    organized_pairs[market_type] = []
                
                # Remover prefixo do tipo para pares não-binary se já estiver no nome
                display_name = pair
                if market_type != "binary" and pair.startswith(f"{market_type.upper()}_"):
                    display_name = pair.split("_", 1)[1]
                
                organized_pairs[market_type].append(display_name)
            
            pairs_data = {
                "timestamp": time.time(),
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pairs": list(self.available_pairs.keys()),
                "organized": organized_pairs
            }
            
            frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
            os.makedirs(frontend_dir, exist_ok=True)
            
            with open(os.path.join(frontend_dir, "available_pairs.json"), "w") as f:
                json.dump(pairs_data, f, indent=2)
                
            logger.info(f"Arquivo de pares disponíveis salvo com {len(self.available_pairs)} pares")
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo de pares: {str(e)}")
            
    def get_available_pairs(self):
        """Retorna a lista de pares disponíveis"""
        return list(self.available_pairs.keys())
        
    def is_pair_available(self, pair):
        """Verifica se um par específico está disponível"""
        if pair == "TODOS":
            return len(self.available_pairs) > 0
        return pair in self.available_pairs
        
    def get_best_pair(self):
        """Retorna o melhor par para operar (implementação simplificada)"""
        pairs = list(self.available_pairs.keys())
        if not pairs:
            return None
        # Implementação básica - retorna o primeiro disponível
        return pairs[0]
        
    async def is_pair_available_async(self, pair):
        """Verifica se um par específico está disponível (versão assíncrona)"""
        if pair == "TODOS":
            return True
            
        if not self.iq_bot or not hasattr(self.iq_bot, 'api'):
            logger.warning("IQ Bot não inicializado para verificar par")
            return False
            
        try:
            all_pairs = self.iq_bot.api.get_all_open_time()
            if not all_pairs or "binary" not in all_pairs:
                logger.warning(f"Erro ao verificar disponibilidade do par {pair}")
                return False
                
            if pair in all_pairs["binary"]:
                return all_pairs["binary"][pair]["open"]
            return False
                
        except Exception as e:
            logger.error(f"Erro ao verificar disponibilidade do par {pair}: {str(e)}")
            return False
