import asyncio
import websockets
import json
import traceback
import sys
import os
import time
import random
from debug_tools import setup_logging, log_api_response
import argparse
import traceback
import logging  # Adicionando import de logging que estava faltando
from pair_monitor import PairMonitor
import ssl
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

# Verificando se o pacote iqoptionapi está instalado
try:
    from iq import IQBot
    print("✅ Biblioteca IQBot importada com sucesso!")
except ImportError as e:
    print("\n❌ ERRO: Não foi possível importar o módulo IQBot")
    print(f"Detalhes: {str(e)}")
    print("\nPara resolver este problema:")
    print("1. Execute o arquivo 'install_dependencies.py' na pasta do projeto")
    print("2. Ou execute o comando: pip install -U git+https://github.com/iqoptionapi/iqoptionapi.git")
    print("\nVerifique se o arquivo iq.py está no mesmo diretório que bot.py")
    sys.exit(1)

# Substitua por seus dados reais da IQ Option
EMAIL = "lucasbretzke@gmail.com"
SENHA = "@Ma78su05"

# Aviso de segurança para credenciais
print("\n[⚠️] AVISO: Suas credenciais estão visíveis no código fonte!")
print("[⚠️] Recomenda-se utilizar variáveis de ambiente ou arquivo .env para armazená-las de forma segura.\n")

config = {
    "ligado": False,
    "valor": 2,
    "par": "EURUSD",
    "direcao": "call",
    "martingale": True,
    "multiplicador": 2,
    "max_mg": 2,
    "tempo": 5,
    "tipo_conta": "PRACTICE"  # Padrão para conta demo
}

# Lista de pares mais confiáveis e comuns (atualizar conforme necessário)
PARES_CONFIÁVEIS = [
    "EURUSD", "EURGBP", "GBPUSD", "USDCHF", "EURCHF", "AUDUSD", 
    "NZDUSD", "USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "USDJPY", 
    "EURAUD", "EURCAD", "USDCAD"
]

# Setup de argumentos de linha de comando
parser = argparse.ArgumentParser(description='IQ Option Trading Bot')
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
parser.add_argument('--auto-update-pairs', action='store_true', help='Automatically update available pairs')
args = parser.parse_args()

# Configure o logging
logger = setup_logging()

iq = None
connected_clients = set()
pair_monitor = None

def ensure_log_directory():
    """Garante que o diretório de logs existe"""
    # Usa o diretório atual do script como base
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "logs")
    
    # Cria o diretório se não existir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"[i] Diretório de logs criado: {log_dir}")
    
    return log_dir

async def get_available_pairs():
    """Retorna os pares de moedas disponíveis para o cliente"""
    global iq, pair_monitor
    
    all_pairs = []
    
    try:
        if iq is None:
            logger.warning("IQ não inicializado ao obter pares disponíveis")
            return ["EURUSD", "USDJPY"]  # Pares padrão como fallback
            
        # Obter pares de todos os mercados disponíveis
        all_open_time = iq.api.get_all_open_time()
        
        # Processar cada tipo de mercado
        for market_type in ["binary", "turbo", "digital"]:
            if market_type in all_open_time:
                logger.info(f"Processando mercado: {market_type}")
                
                # Para o tipo digital, usamos abordagem diferente
                if market_type == "digital":
                    try:
                        if hasattr(iq.api, 'get_digital_underlying'):
                            digital_pairs = iq.api.get_digital_underlying()
                            logger.info(f"Encontrados {len(digital_pairs)} pares digitais")
                            
                            for pair_name in digital_pairs:
                                digital_pair = f"DIGITAL_{pair_name}"
                                if digital_pair not in all_pairs:
                                    all_pairs.append(digital_pair)
                    except Exception as e:
                        logger.error(f"Erro ao obter pares digitais: {str(e)}")
                else:
                    # Processamento para pares regulares (binary, turbo)
                    for pair_name, pair_status in all_open_time[market_type].items():
                        # Verificar se é dict ou booleano
                        is_open = False
                        if isinstance(pair_status, dict) and "open" in pair_status:
                            is_open = pair_status["open"]
                        elif isinstance(pair_status, bool):
                            is_open = pair_status
                            
                        if is_open:
                            # Adicionar prefixo apenas para pares não binários para evitar confusão
                            formatted_name = pair_name
                            if market_type != "binary":
                                formatted_name = f"{market_type.upper()}_{pair_name}"
                                
                            if formatted_name not in all_pairs:
                                all_pairs.append(formatted_name)
        
        # Buscar também por pares OTC
        try:
            binary_pairs = all_open_time.get("binary", {})
            otc_pairs = [pair for pair in binary_pairs if "OTC" in pair and binary_pairs[pair].get("open", False)]
            logger.info(f"Encontrados {len(otc_pairs)} pares OTC")
            
            for pair in otc_pairs:
                if pair not in all_pairs:
                    all_pairs.append(pair)
        except Exception as e:
            logger.error(f"Erro ao processar pares OTC: {str(e)}")
                    
        logger.info(f"Total de {len(all_pairs)} pares disponíveis")
        
        # Salvar pares para diagnóstico
        try:
            log_dir = ensure_log_directory()
            with open(os.path.join(log_dir, "available_pairs.json"), "w") as f:
                json.dump({
                    "timestamp": time.time(),
                    "pairs": all_pairs,
                    "raw_data": all_open_time
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar pares para diagnóstico: {str(e)}")
            
        return all_pairs
    except Exception as e:
        logger.error(f"Erro ao obter pares disponíveis: {str(e)}")
        return ["EURUSD", "USDJPY"]  # Fallback em caso de erro

async def verificar_par_disponivel(par, iq):
    """Verifica se um par específico está disponível para negociação"""
    # Caso especial para a opção "TODOS"
    if par.upper() == "TODOS":
        # Para "TODOS", retorne True, pois não é um par específico, 
        # mas uma instrução para monitorar todos os pares
        return True
    
    # Verificar se iq está inicializado
    if iq is None:
        print("❌ IQ não inicializado ao verificar disponibilidade do par")
        return False
    
    try:
        # Comportamento existente para verificação de pares reais
        all_open_time = iq.api.get_all_open_time()  # Corrigindo acesso à API
        
        # Verifica se o par existe e está disponível
        for market in ["binary", "turbo", "digital"]:
            if market in all_open_time:
                if par in all_open_time[market]:
                    if all_open_time[market][par]["open"]:
                        return True
        
        # Se chegou aqui, o par não está disponível
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar disponibilidade do par {par}: {str(e)}")
        return False

async def analisar_tendencia(par):
    """Análise de tendência com suporte para 'TODOS'"""
    global pair_monitor, iq
    
    par_operacao = par  # Criar uma variável para armazenar o par que será efetivamente usado
    
    if par.upper() == "TODOS":
        # Primeiro, tentar obter um par confiável que esteja disponível
        try:
            if iq is not None:
                all_pairs = iq.api.get_all_open_time()
                if "binary" in all_pairs:
                    # Primeiro tenta usar pares confiáveis
                    for safe_pair in PARES_CONFIÁVEIS:
                        if safe_pair in all_pairs["binary"] and all_pairs["binary"][safe_pair]["open"]:
                            par_operacao = safe_pair
                            await notify_clients(f"Selecionado par confiável {safe_pair} para operação")
                            print(f"[✅] Usando par confiável {safe_pair}")
                            break
                    
                    # Se não encontrou nenhum par confiável, vai para plano B
                    if par_operacao == "TODOS" and pair_monitor and hasattr(pair_monitor, 'get_best_pair'):
                        best_pair = pair_monitor.get_best_pair()
                        if best_pair:
                            # Verifica se o par realmente é suportado pelo sistema antes de usar
                            if iq.verificar_par_suportado(best_pair):
                                await notify_clients(f"Selecionado par {best_pair} para operação")
                                par_operacao = best_pair
                                print(f"[✅] Usando par recomendado pelo monitor: {best_pair}")
                            else:
                                print(f"[⚠️] Par {best_pair} não é suportado, buscando alternativa")
        except Exception as e:
            logger.error(f"Erro ao buscar par alternativo no modo TODOS: {e}")
            # Se ocorrer erro ao selecionar par automaticamente, use EURUSD (geralmente disponível)
            par_operacao = "EURUSD"
            await notify_clients(f"Erro ao selecionar par, usando EURUSD como padrão")
            print(f"[⚠️] Usando EURUSD como último recurso: {e}")
    
    # Simulação simples: aleatório para exemplo
    direcao = random.choice(["call", "put"])
    print(f"[📈] Tendência detectada: {direcao.upper()} para {par_operacao}")
    return direcao, par_operacao  # Retornar tanto a direção quanto o par usado

async def executar_robô():
    global config, iq

    while True:
        try:
            if config["ligado"] and iq is not None:
                # Verificar se o mercado está aberto
                pares_abertos = iq.api.get_all_open_time()
                if args.debug:
                    log_api_response(pares_abertos, "get_all_open_time")
                
                par = config["par"]
                
                # Tratamento especial para o modo "TODOS"
                if par.upper() == "TODOS":
                    # Para o modo "TODOS", vamos selecionar um par disponível através do pair_monitor
                    direcao_tendencia, par_escolhido = await analisar_tendencia(par)
                    
                    if par_escolhido == "TODOS":
                        # Se analisar_tendencia também retornou TODOS, não temos pares disponíveis
                        await notify_clients("⚠️ Modo TODOS ativado mas nenhum par disponível encontrado")
                        await asyncio.sleep(30)  # Espera antes de tentar novamente
                        continue
                    
                    # Usar o par escolhido pelo analisador
                    par_atual = par_escolhido
                else:
                    # Para um par específico, verificar disponibilidade
                    if not await verificar_par_disponivel(par, iq):
                        await notify_clients(f"⚠️ O par {par} não está disponível para negociação agora")
                        await asyncio.sleep(30)  # Espera antes de tentar novamente
                        continue
                    
                    direcao_tendencia, _ = await analisar_tendencia(par)
                    par_atual = par
                
                # Na versão de exemplo, usamos a tendência como direção de operação
                direcao_operar = direcao_tendencia
                
                logger.info(f"Executando operação: {direcao_operar} em {par_atual}")
                await notify_clients(f"Operando: {direcao_operar.upper()} em {par_atual}")
                
                # Configure antes de cada operação (usar o par correto)
                iq.definir_config(par_atual, config["tempo"], config["valor"], config["tipo_conta"])
                
                # Tentativa de operação com tratamento de exceção
                try:
                    success, resultado = iq.entrar(direcao_operar, 
                                martingale=config["martingale"],
                                multiplicador=config["multiplicador"], 
                                max_mg=config["max_mg"])
                                
                    if success:
                        await notify_clients(f"✅ Operação bem-sucedida! Lucro: {resultado}")
                    else:
                        await notify_clients(f"❌ Operação falhou. Resultado: {resultado}")
                        
                except Exception as trade_err:
                    error_msg = f"Erro na operação: {str(trade_err)}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    await notify_clients(error_msg)
                
                # Aguarda entre operações
                await asyncio.sleep(config["tempo"] * 10)
                
        except Exception as e:
            error_msg = f"Erro durante execução do robô: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            await notify_clients(error_msg)
            
        await asyncio.sleep(5)

async def notify_clients(message):
    """Envia uma mensagem para todos os clientes conectados com tratamento melhorado de erros"""
    if connected_clients:
        data = json.dumps({"status": "info", "msg": message})
        
        # Usar uma lista para rastrear clientes com erro
        problem_clients = []
        
        for client in connected_clients:
            try:
                await client.send(data)
            except Exception as e:
                print(f"Erro ao enviar mensagem para cliente: {e}")
                problem_clients.append(client)
        
        # Remover clientes problemáticos da lista
        for client in problem_clients:
            if client in connected_clients:
                connected_clients.remove(client)
                print(f"Cliente removido da lista devido a erro de comunicação")

async def websocket_heartbeat(websocket):
    """Envia heartbeats periódicos para manter a conexão ativa"""
    try:
        counter = 0
        while True:
            # A cada 15 segundos, enviar um heartbeat completo (reduzido de 30 segundos)
            await websocket.send(json.dumps({
                "status": "heartbeat",
                "counter": counter,
                "timestamp": time.time()
            }))
            counter += 1
            
            # Fazer sleep em intervalos menores para responder mais rapidamente
            # se a tarefa for cancelada
            for _ in range(15):  # 15 intervalos de 1 segundo = 15 segundos total
                await asyncio.sleep(1)
    except (ConnectionClosedError, ConnectionClosedOK, asyncio.CancelledError):
        # Conexão fechada normalmente, não precisa logar
        pass
    except Exception as e:
        logger.error(f"Erro no heartbeat: {e}")

async def handler(websocket):
    global config, iq, connected_clients, pair_monitor
    
    # Adiciona o cliente à lista de conexões
    client_id = id(websocket)  # ID único para este cliente
    connected_clients.add(websocket)
    print(f"[+] Cliente conectado (ID: {client_id}). Total de clientes: {len(connected_clients)}")
    
    # Iniciar tarefa de heartbeat para manter a conexão
    heartbeat_task = asyncio.create_task(websocket_heartbeat(websocket))
    
    try:
        # Aqui colocamos tratamento para suprimir erros de conexão
        try:
            # Envia informação de diagnóstico sobre o status do sistema
            await websocket.send(json.dumps({
                "status": "info",
                "msg": f"Conectado ao servidor. Status do pair_monitor: {'Ativo' if pair_monitor else 'Inativo'}",
                "robo_status": config["ligado"]  # Enviar status atual do robô
            }))
        except (ConnectionClosedError, ConnectionClosedOK):
            # Cliente já desconectou, finalizar handler
            return
        
        # Adicionar TODOS à lista de pares disponíveis
        if pair_monitor:
            try:
                pairs = pair_monitor.get_available_pairs()
                if pairs:
                    # Adiciona "TODOS" como primeiro item
                    pairs_with_todos = ["TODOS"] + pairs
                    await websocket.send(json.dumps({
                        "status": "pairs_list",
                        "pairs": pairs_with_todos
                    }))
                    print(f"Enviados {len(pairs_with_todos)} pares (incluindo TODOS) para o cliente")
            except Exception as e:
                print(f"Erro ao enviar pares iniciais: {str(e)}")
        
        # Usar uma variável para controlar a frequência de atualizações
        last_update_time = 0
        min_update_interval = 1  # Reduzido para 1 segundo (era 5)
        
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Tratar comando de ping separadamente (mais leve)
                if "command" in data and data["command"] == "ping":
                    await websocket.send(json.dumps({"status": "pong", "timestamp": time.time()}))
                    continue
                
                # Para outros comandos, mostra detalhes completos
                print(f"[📩] Recebido {len(message)} bytes do cliente {client_id}")
                print(f"[📩] Conteúdo: {data}")
                
                # Comando para verificar disponibilidade de um par específico
                if "command" in data and data["command"] == "check_pair_availability" and "pair" in data:
                    pair = data["pair"]
                    is_available = await verificar_par_disponivel(pair, iq)
                    await websocket.send(json.dumps({
                        "status": "pair_availability",
                        "pair": pair,
                        "available": is_available
                    }))
                    continue
                
                # Comando especial para obter pares disponíveis
                if "command" in data and data["command"] == "get_available_pairs":
                    last_update_time = time.time()
                    print(f"Recebida solicitação para atualizar pares disponíveis do cliente {client_id}")
                    
                    # Flag para incluir todos os mercados
                    include_all_markets = data.get("include_all_markets", False)
                    
                    try:
                        # Atualizar pares via função dedicada
                        print("Obtendo lista completa de pares disponíveis...")
                        all_pairs = await get_available_pairs()
                        
                        # Adiciona "TODOS" como primeiro item
                        all_pairs_with_todos = ["TODOS"] + all_pairs
                        
                        print(f"Enviando {len(all_pairs)} pares disponíveis para o cliente")
                        
                        await websocket.send(json.dumps({
                            "status": "pairs_list", 
                            "pairs": all_pairs_with_todos,
                            "count": len(all_pairs),
                            "timestamp": time.time()
                        }))
                    except Exception as e:
                        print(f"Erro ao obter pares disponíveis: {str(e)}")
                        await websocket.send(json.dumps({
                            "status": "error", 
                            "msg": f"Erro ao obter pares disponíveis: {str(e)}"
                        }))
                    continue
                
                # Atualiza a configuração
                for key in config:
                    if key in data:
                        config[key] = data[key]

                # Inicializa o bot se ainda não foi feito
                if not iq:
                    try:
                        print("[🚀] Inicializando bot IQ Option...")
                        iq = IQBot(EMAIL, SENHA)
                        
                        # Verificar se a conexão está ativa
                        if not iq.check_connect():
                            await websocket.send(json.dumps({
                                "status": "erro", 
                                "msg": "Falha na conexão com a IQ Option. Tente novamente."
                            }))
                            continue
                        
                        # Configure o tipo de conta ao conectar
                        if "tipo_conta" in data:
                            iq.mudar_tipo_conta(data["tipo_conta"])
                            if data["tipo_conta"] == "REAL":
                                await websocket.send(json.dumps({
                                    "status": "aviso", 
                                    "msg": "⚠️ CONECTADO EM CONTA REAL - Use com responsabilidade ⚠️"
                                }))
                                
                        # Inicializa o monitor de pares depois de conectar o IQ
                        if args.auto_update_pairs:
                            pair_monitor = PairMonitor(iq)
                            await pair_monitor.start_monitoring()
                            
                            # Envie a lista inicial para o cliente
                            pairs = await pair_monitor.update_available_pairs()
                            await websocket.send(json.dumps({
                                "status": "pairs_list", 
                                "pairs": pairs
                            }))
                                
                        await websocket.send(json.dumps({
                            "status": "ok", 
                            "msg": f"Bot conectado! Saldo: {iq.obter_saldo()}"
                        }))
                    except Exception as e:
                        print(f"[❌] Erro ao inicializar bot: {str(e)}")
                        await websocket.send(json.dumps({
                            "status": "erro", 
                            "msg": f"Erro ao conectar na IQ Option: {str(e)}"
                        }))
                        continue
                
                # Muda o tipo de conta se necessário
                elif "tipo_conta" in data:
                    iq.mudar_tipo_conta(data["tipo_conta"])
                    if data["tipo_conta"] == "REAL":
                        await websocket.send(json.dumps({
                            "status": "aviso", 
                            "msg": "⚠️ MUDANDO PARA CONTA REAL ⚠️"
                        }))
                    else:
                        await websocket.send(json.dumps({
                            "status": "aviso", 
                            "msg": "Mudando para conta DEMO"
                        }))

                await websocket.send(json.dumps({
                    "status": "ok", 
                    "msg": "Configuração atualizada"
                }))
                
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "status": "erro", 
                    "msg": "Formato de dados inválido"
                }))
                
            except (ConnectionClosedError, ConnectionClosedOK):
                # O cliente foi desconectado durante o processamento, encerre o handler
                print(f"[i] Cliente {client_id} desconectado durante processamento")
                return
                
            except Exception as e:
                print(f"[❌] Erro ao processar mensagem do cliente {client_id}: {str(e)}")
                try:
                    await websocket.send(json.dumps({
                        "status": "erro", 
                        "msg": f"Erro: {str(e)}"
                    }))
                except (ConnectionClosedError, ConnectionClosedOK):
                    # Cliente já desconectou, encerre o handler
                    return
    
    except (ConnectionClosedError, ConnectionClosedOK):
        print(f"[i] Conexão fechada pelo cliente {client_id}")
    except Exception as e:
        print(f"[!] Erro na conexão com cliente {client_id}: {str(e)}")
        logger.error(f"Erro no WebSocket: {str(e)}")
        logger.error(traceback.format_exc())
    
    finally:
        # Cancelar heartbeat de forma segura
        try:
            heartbeat_task.cancel()
            await asyncio.shield(asyncio.sleep(0))  # Dar chance para o cancelamento ser processado
        except:
            pass
        
        # Remove o cliente da lista quando desconectar
        if websocket in connected_clients:
            connected_clients.remove(websocket)
            print(f"[-] Cliente {client_id} desconectado. Total de clientes: {len(connected_clients)}")

async def start_server():
    """Inicializa o servidor WebSocket com configurações otimizadas"""
    print("[🚀] Iniciando servidor WebSocket na porta 6789...")
    
    # Configurar o servidor com parâmetros otimizados de conexão
    server = await websockets.serve(
        handler, 
        "localhost", 
        6789,
        ping_interval=20,       # Envia ping a cada 20 segundos
        ping_timeout=30,        # Timeout do ping aumentado para 30 segundos
        close_timeout=30,       # Timeout para fechamento de conexão aumentado
        max_size=10485760,      # 10MB de tamanho máximo de mensagem
        max_queue=64,           # Aumentado o tamanho da fila de mensagens
        compression=None        # Desabilitar compressão para reduzir sobrecarga
    )
    
    print("[✅] Servidor WebSocket iniciado e aguardando conexões")
    return server

async def main():
    print("[i] Iniciando Robô Trader v2.0...")
    
    # Garantir que o diretório de logs exista antes de iniciar
    ensure_log_directory()
    
    # Iniciar o servidor WebSocket com configurações otimizadas
    server = await start_server()
    
    # Inicia a tarefa do robô
    bot_task = asyncio.create_task(executar_robô())
    
    # Mantém o servidor rodando indefinidamente
    await asyncio.Future()

if __name__ == "__main__":
    try:
        if args.debug:
            print("Modo de debug ativado. Logs detalhados serão salvos.")
            logger.setLevel(logging.DEBUG)
        
        # Garantir que o diretório de logs exista antes de iniciar
        ensure_log_directory()
        
        asyncio.run(main())
    except KeyboardInterrupt:
        # Adicione limpeza
        if pair_monitor:
            asyncio.run(pair_monitor.stop_monitoring())
        print("\n[👋] Servidor encerrado pelo usuário")
    except Exception as e:
        print(f"\n[❌] Erro: {str(e)}")
        traceback.print_exc()
