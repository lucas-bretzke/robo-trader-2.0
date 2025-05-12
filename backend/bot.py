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
    
    if not pair_monitor or not iq:
        return ["EURUSD", "USDJPY"]  # Pares padrão como fallback
        
    try:
        pairs = await pair_monitor.update_available_pairs()
        return pairs
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
    """Envia uma mensagem para todos os clientes conectados"""
    if connected_clients:
        data = json.dumps({"status": "info", "msg": message})
        await asyncio.gather(*[client.send(data) for client in connected_clients])

async def websocket_heartbeat(websocket):
    """Envia heartbeats periódicos para manter a conexão ativa"""
    try:
        counter = 0
        while True:
            # A cada 30 segundos, enviar um heartbeat completo
            await websocket.send(json.dumps({
                "status": "heartbeat",
                "counter": counter,
                "timestamp": time.time()
            }))
            counter += 1
            
            # Fazer sleep em intervalos menores para responder mais rapidamente
            # se a tarefa for cancelada
            for _ in range(30):
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
                "msg": f"Conectado ao servidor. Status do pair_monitor: {'Ativo' if pair_monitor else 'Inativo'}"
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
                print(f"[📩] Recebido {len(message)} bytes do cliente {client_id}")
                
                # Tratar comando de ping separadamente (mais leve)
                if "command" in data and data["command"] == "ping":
                    await websocket.send(json.dumps({"status": "pong"}))
                    continue
                
                # Para outros comandos, mostra detalhes completos
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
                    # NÃO bloquear atualizações frequentes - isso pode causar problemas no frontend
                    # O WebSocket deve ser stateless e responder a todas as solicitações
                    last_update_time = time.time()  # Atualizar timestamp para registro
                    print(f"Recebida solicitação para atualizar pares disponíveis do cliente {client_id}")
                    
                    # Tenta usar o pair_monitor se estiver disponível
                    if pair_monitor:
                        try:
                            print("Atualizando pares via pair_monitor...")
                            pairs = await pair_monitor.update_available_pairs()
                            print(f"Encontrados {len(pairs)} pares disponíveis")
                            
                            # Adiciona "TODOS" como primeiro item
                            pairs_with_todos = ["TODOS"] + pairs
                            
                            await websocket.send(json.dumps({
                                "status": "pairs_list", 
                                "pairs": pairs_with_todos
                            }))
                        except Exception as e:
                            print(f"Erro ao atualizar pares via pair_monitor: {str(e)}")
                            await websocket.send(json.dumps({
                                "status": "error", 
                                "msg": f"Erro ao obter pares: {str(e)}"
                            }))
                    # Fallback: tentar obter pares diretamente
                    elif iq:
                        try:
                            print("Obtendo pares diretamente via API...")
                            all_pairs = iq.api.get_all_open_time()
                            
                            # Garantir que o diretório de logs existe
                            log_dir = ensure_log_directory()
                            pairs_file = os.path.join(log_dir, "pairs_direct.json")
                            
                            # Salvar para debug
                            with open(pairs_file, "w") as f:
                                json.dump(all_pairs, f, indent=2)
                            
                            available_pairs = []
                            if "binary" in all_pairs:
                                for pair, status in all_pairs["binary"].items():
                                    if status["open"]:
                                        available_pairs.append(pair)
                            
                            # Adiciona "TODOS" como primeiro item
                            available_pairs = ["TODOS"] + available_pairs
                                        
                            print(f"Encontrados {len(available_pairs)-1} pares diretamente")
                            await websocket.send(json.dumps({
                                "status": "pairs_list", 
                                "pairs": available_pairs
                            }))
                        except Exception as e:
                            print(f"Erro ao obter pares diretamente: {str(e)}")
                            await websocket.send(json.dumps({
                                "status": "error", 
                                "msg": f"Erro ao obter pares: {str(e)}"
                            }))
                    else:
                        # Se não temos nenhuma fonte de pares, retornar pelo menos "TODOS"
                        await websocket.send(json.dumps({
                            "status": "pairs_list", 
                            "pairs": ["TODOS", "EURUSD", "USDJPY"]
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
            await asyncio.sleep(0)  # Dar chance para o cancelamento ser processado
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
        ping_interval=30,       # Envia ping a cada 30 segundos
        ping_timeout=10,        # Timeout do ping em 10 segundos
        close_timeout=10,       # Timeout para fechamento de conexão
        max_size=10485760,      # 10MB de tamanho máximo de mensagem
        max_queue=32            # Tamanho da fila de mensagens
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
