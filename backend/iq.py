# Adicionando tratamento de erros para importar a biblioteca IQOptionAPI
try:
    from iqoptionapi.stable_api import IQ_Option
except ImportError:
    print("====================================================")
    print("ERRO: Biblioteca IQOptionAPI não encontrada!")
    print("\nPara instalar, execute o comando:")
    print("pip install -U git+https://github.com/iqoptionapi/iqoptionapi.git")
    print("\nOu execute o arquivo 'install_dependencies.py' na pasta do projeto.")
    print("====================================================")
    import sys
    sys.exit(1)
    
import time
import logging
import sys
import os

# Adicione o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from debug_tools import log_api_response, log_trade_attempt

# Configuração de logging para depurar erros de conexão
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Logger específico para esta classe
logger = logging.getLogger('iq_bot')

class IQBot:
    def __init__(self, email, senha):
        self.email = email
        self.senha = senha
        
        try:
            print("Conectando à IQ Option...")
            self.api = IQ_Option(email, senha)
            self.status, self.reason = self.api.connect()
            
            if not self.status:
                raise Exception(f"Erro ao conectar na IQ Option: {self.reason}")
            print("Conexão estabelecida com sucesso!")
            
            # Por padrão, usa conta demo
            self.api.change_balance('PRACTICE')
            print(f"Tipo de conta: DEMO (Prática)")
            print(f"Saldo atual: {self.obter_saldo()}")
            
        except Exception as e:
            print(f"Erro ao inicializar o bot: {str(e)}")
            raise
        
    def mudar_tipo_conta(self, tipo_conta):
        """
        Muda o tipo de conta (PRACTICE para demo, REAL para conta real)
        """
        if tipo_conta in ['PRACTICE', 'REAL']:
            self.api.change_balance(tipo_conta)
            print(f"[💼] Tipo de conta alterado para: {tipo_conta}")
            print(f"[💰] Saldo disponível: {self.obter_saldo()}")
            return True
        return False

    def definir_config(self, par, tempo, entrada, tipo_conta='PRACTICE'):
        self.par = par
        self.tempo = tempo
        self.entrada = entrada
        # Atualiza o tipo de conta se necessário
        self.mudar_tipo_conta(tipo_conta)
        print(f"[⚙️] Configuração definida: {par}, {tempo}min, ${entrada}")

    def obter_saldo(self):
        return self.api.get_balance()

    def verificar_direcao(self, direcao):
        direcao = direcao.lower()
        return "call" if direcao == "call" else "put"

    def verificar_par_suportado(self, par):
        """Verifica se um par é suportado pela API IQ Option"""
        try:
            # Verifica se é par digital (formato DIGITAL_EURUSD)
            if par.startswith("DIGITAL_"):
                # Extrair o par subjacente (EURUSD da parte DIGITAL_EURUSD)
                underlying = par.split("_", 1)[1]
                
                # Verificar se o subjacente está nos ativos digitais disponíveis
                if hasattr(self.api, 'get_digital_underlying'):
                    available_digital = self.api.get_digital_underlying()
                    return underlying in available_digital
                return False
            
            # Verifica se é par de outro mercado específico (formato TURBO_EURUSD, CFD_EURUSD, etc.)
            if "_" in par:
                market, underlying = par.split("_", 1)
                
                # Verificar se o mercado existe e se o par está disponível nele
                all_pairs = self.api.get_all_open_time()
                market = market.lower()
                if market in all_pairs and underlying in all_pairs[market]:
                    return all_pairs[market][underlying]["open"] if isinstance(all_pairs[market][underlying], dict) else all_pairs[market][underlying]
                return False
                
            # Pares regulares (binário/turbo) - verificação padrão
            # Verifica se o par está nos ativos conhecidos pela API
            from iqoptionapi.constants import OP_code
            is_known = par in OP_code.ACTIVES
            
            # Verificação adicional para garantir que o par está disponível
            if is_known:
                all_pairs = self.api.get_all_open_time()
                for market in ["binary", "turbo"]:
                    if market in all_pairs and par in all_pairs[market]:
                        is_available = all_pairs[market][par]["open"] if isinstance(all_pairs[market][par], dict) else all_pairs[market][par]
                        if is_available:
                            return True
            
            # Verificar outras possibilidades para o par
            return self.check_alternative_markets(par)
            
        except Exception as e:
            print(f"[⚠️] Erro ao verificar se o par {par} é suportado: {str(e)}")
            logger.error(f"Erro ao verificar par {par}: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def check_alternative_markets(self, par):
        """Verifica se um par está disponível em mercados alternativos"""
        try:
            # Tentar mercados diferentes para o mesmo par
            all_pairs = self.api.get_all_open_time()
            available_markets = all_pairs.keys()
            
            # Logar os mercados disponíveis para debug
            logger.debug(f"Mercados disponíveis: {available_markets}")
            
            for market in available_markets:
                if market != "binary" and par in all_pairs[market]:
                    is_available = all_pairs[market][par]["open"] if isinstance(all_pairs[market][par], dict) else all_pairs[market][par]
                    if is_available:
                        logger.info(f"Par {par} encontrado disponível no mercado {market}")
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar mercados alternativos: {str(e)}")
            return False
    
    def check_connect(self):
        """Verifica se a conexão com a API está ativa"""
        try:
            return self.api.check_connect()
        except:
            return False

    def entrar(self, direcao, martingale=False, multiplicador=2, max_mg=2):
        direcao = self.verificar_direcao(direcao)
        tentativa = 0
        valor = self.entrada

        while tentativa <= max_mg:
            try:
                # Registra a tentativa para debug
                log_trade_attempt(self.par, direcao, valor, self.tempo)
                
                # Tratamento especial para o modo "TODOS"
                if self.par.upper() == "TODOS":
                    print(f"[⚠️] ERRO: Não é possível operar diretamente no modo TODOS")
                    return False, 0
                
                # Verificar se é um par digital
                is_digital = self.par.startswith("DIGITAL_")
                
                # Verificar se o par está disponível - com tratamento para diferentes tipos
                disponivel = False
                
                if is_digital:
                    # Extrair nome do par sem prefixo DIGITAL_
                    underlying = self.par.split("_", 1)[1]
                    try:
                        digital_availables = self.api.get_digital_underlying()
                        disponivel = underlying in digital_availables
                        print(f"[i] Par digital {underlying} verificado. Disponível: {disponivel}")
                    except Exception as e:
                        print(f"[⚠️] Erro ao verificar disponibilidade do par digital {underlying}: {str(e)}")
                else:
                    # Para outros tipos de pares, verificar normalmente
                    pares_abertos = self.api.get_all_open_time()
                    log_api_response(pares_abertos, "get_all_open_time")
                    
                    # Verificar se é um par de mercado específico (TURBO_XYZ, CFD_XYZ)
                    if "_" in self.par:
                        market, underlying = self.par.split("_", 1)
                        market = market.lower()
                        
                        if market in pares_abertos and underlying in pares_abertos[market]:
                            disponivel = pares_abertos[market][underlying]["open"] if isinstance(pares_abertos[market][underlying], dict) else pares_abertos[market][underlying]
                    else:
                        # Verificação padrão para pares binários
                        if "binary" in pares_abertos and self.par in pares_abertos['binary']:
                            disponivel = pares_abertos['binary'][self.par]["open"] if isinstance(pares_abertos['binary'][self.par], dict) else pares_abertos['binary'][self.par]
                        elif "turbo" in pares_abertos and self.par in pares_abertos['turbo']:
                            disponivel = pares_abertos['turbo'][self.par]["open"] if isinstance(pares_abertos['turbo'][self.par], dict) else pares_abertos['turbo'][self.par]
                
                if not disponivel:
                    print(f"[❌] ERRO: Par {self.par} não está disponível para negociação")
                    return False, 0
                
                print(f"[i] Par {self.par} está disponível para negociação")
                
                # Executa a operação de acordo com o tipo de par
                if is_digital:
                    # Operação para opções digitais
                    underlying = self.par.split("_", 1)[1]
                    print(f"[i] Tentando realizar operação DIGITAL: {direcao.upper()} em {underlying} com valor {valor}")
                    
                    # Opções digitais usam um método diferente
                    status, id = self.api.buy_digital_spot(underlying, valor, direcao, self.tempo)
                else:
                    # Operação para opções binárias tradicionais
                    print(f"[i] Tentando realizar operação: {direcao.upper()} em {self.par} com valor {valor}")
                    status, id = self.api.buy(valor, self.par, direcao, self.tempo)
                
                log_api_response({"status": status, "id": id}, "buy")
                
                if status:
                    print(f"[+] Entrada: {valor} | Direção: {direcao.upper()} | Tentativa: {tentativa}")
                    # Espere pelo resultado com timeout adequado
                    timeout = self.tempo * 60 + 30  # tempo em segundos + 30s de margem
                    start_time = time.time()
                    
                    while time.time() - start_time < timeout:
                        resultado = self.api.check_win_v4(id)
                        if resultado is not None and resultado != 0:
                            break
                        time.sleep(1)

                    if resultado > 0:
                        print(f"[✔️] Vitória: {resultado}")
                        return True, resultado
                    else:
                        print(f"[❌] Derrota: {resultado}")
                        if martingale:
                            valor *= multiplicador
                            tentativa += 1
                            if tentativa > max_mg:
                                return False, resultado
                            print(f"[🔄] Aplicando Martingale: Nova entrada {valor}")
                        else:
                            return False, resultado
                else:
                    print("[!] Erro ao fazer entrada")
                    log_api_response(self.api.get_api_error() if hasattr(self.api, 'get_api_error') else "Unknown error", "api_error")
                    return False, 0
            except Exception as e:
                print(f"[!] Erro durante a operação: {str(e)}")
                import traceback
                traceback.print_exc()
                return False, 0
        
        return False, 0
