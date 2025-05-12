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
from pair_monitor import PairMonitor

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

async def check_pair_availability(pair):
    """Verifica se um par específico está disponível para negociação"""
    global iq
    
    if not iq:
        return False
    
    try:
        all_pairs = iq.api.get_all_open_time()
        if not all_pairs or "binary" not in all_pairs:
            logger.warning(f"Erro ao verificar disponibilidade do par {pair}")
            return False
            
        if pair in all_pairs["binary"]:
            is_available = all_pairs["binary"][pair]["open"]
            logger.info(f"Par {pair}: {'disponível' if is_available else 'indisponível'}")
            return is_available
        else:
            logger.warning(f"Par {pair} não encontrado na lista de pares")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao verificar disponibilidade do par {pair}: {str(e)}")
        return False

async def analisar_tendencia(par):
    """Análise de tendência com suporte para 'TODOS'"""
    global pair_monitor
    
    if par == "TODOS" and pair_monitor:
        # Se estiver no modo "TODOS", escolhe um par disponível
        best_pair = pair_monitor.get_best_pair()
        if best_pair:
            await notify_clients(f"Selecionado par {best_pair} para operação")
            par = best_pair
    
    # Simulação simples: aleatório para exemplo
    direcao = random.choice(["call", "put"])
    print(f"[📈] Tendência detectada: {direcao.upper()}")
    return direcao

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
                
                # Verificar se o par está disponível para operação
                if not par in pares_abertos["binary"] or not pares_abertos["binary"][par]["open"]:
                    await notify_clients(f"⚠️ O par {par} não está disponível para negociação agora")
                    await asyncio.sleep(30)  # Espera antes de tentar novamente
                    continue
                    
                direcao_tendencia = await analisar_tendencia(config["par"])
                
                # Na versão de exemplo, usamos a tendência como direção de operação
                direcao_operar = direcao_tendencia
                
                logger.info(f"Executando operação: {direcao_operar} em {config['par']}")
                await notify_clients(f"Operando: {direcao_operar.upper()} em {config['par']}")
                
                # Configure antes de cada operação
                iq.definir_config(config["par"], config["tempo"], config["valor"], config["tipo_conta"])
                
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

async def handler(websocket):
    global config, iq, connected_clients, pair_monitor
    
    # Adiciona o cliente à lista de conexões
    connected_clients.add(websocket)
    print(f"[+] Cliente conectado. Total de clientes: {len(connected_clients)}")
    
    try:
        # Envia informação de diagnóstico sobre o status do sistema
        await websocket.send(json.dumps({
            "status": "info",
            "msg": f"Conectado ao servidor. Status do pair_monitor: {'Ativo' if pair_monitor else 'Inativo'}"
        }))
        
        # Se o pair_monitor já estiver inicializado, envia a lista atual
        if pair_monitor:
            try:
                pairs = pair_monitor.get_available_pairs()
                if pairs:
                    await websocket.send(json.dumps({
                        "status": "pairs_list",
                        "pairs": pairs
                    }))
                    print(f"Enviados {len(pairs)} pares para o cliente no momento da conexão")
            except Exception as e:
                print(f"Erro ao enviar pares iniciais: {str(e)}")
        
        async for message in websocket:
            try:
                data = json.loads(message)
                print(f"[📩] Recebido: {data}")
                
                # Comando para verificar disponibilidade de um par específico
                if "command" in data and data["command"] == "check_pair_availability" and "pair" in data:
                    pair = data["pair"]
                    is_available = await check_pair_availability(pair)
                    await websocket.send(json.dumps({
                        "status": "pair_availability",
                        "pair": pair,
                        "available": is_available
                    }))
                    continue
                
                # Comando especial para obter pares disponíveis
                if "command" in data and data["command"] == "get_available_pairs":
                    print("Recebida solicitação para atualizar pares disponíveis")
                    
                    # Tenta usar o pair_monitor se estiver disponível
                    if pair_monitor:
                        try:
                            print("Atualizando pares via pair_monitor...")
                            pairs = await pair_monitor.update_available_pairs()
                            print(f"Encontrados {len(pairs)} pares disponíveis")
                            await websocket.send(json.dumps({
                                "status": "pairs_list", 
                                "pairs": pairs
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
                            
                            # Salvar para debug
                            with open("../logs/pairs_direct.json", "w") as f:
                                json.dump(all_pairs, f, indent=2)
                            
                            available_pairs = []
                            if "binary" in all_pairs:
                                for pair, status in all_pairs["binary"].items():
                                    if status["open"]:
                                        available_pairs.append(pair)
                                        
                            print(f"Encontrados {len(available_pairs)} pares diretamente")
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
                        await websocket.send(json.dumps({
                            "status": "error", 
                            "msg": "Não foi possível obter pares, robot não conectado"
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
                
            except Exception as e:
                print(f"[❌] Erro ao processar mensagem: {str(e)}")
                await websocket.send(json.dumps({
                    "status": "erro", 
                    "msg": f"Erro: {str(e)}"
                }))
    
    except websockets.exceptions.ConnectionClosed:
        print("[i] Conexão fechada pelo cliente")
    
    finally:
        # Remove o cliente da lista quando desconectar
        connected_clients.remove(websocket)
        print(f"[-] Cliente desconectado. Total de clientes: {len(connected_clients)}")

async def main():
    print("[🚀] Servidor WebSocket iniciado na porta 6789")
    print("[i] Aguardando conexões...")
    
    async with websockets.serve(handler, "localhost", 6789):
        # Inicia a tarefa do robô
        bot_task = asyncio.create_task(executar_robô())
        
        # Mantém o servidor rodando indefinidamente
        await asyncio.Future()

if __name__ == "__main__":
    try:
        if args.debug:
            print("Modo de debug ativado. Logs detalhados serão salvos.")
            logger.setLevel(logging.DEBUG)
        
        asyncio.run(main())
    except KeyboardInterrupt:
        # Adicione limpeza
        if pair_monitor:
            asyncio.run(pair_monitor.stop_monitoring())
        print("\n[👋] Servidor encerrado pelo usuário")
    except Exception as e:
        print(f"\n[❌] Erro: {str(e)}")
        traceback.print_exc()
