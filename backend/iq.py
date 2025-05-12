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

    def entrar(self, direcao, martingale=False, multiplicador=2, max_mg=2):
        direcao = self.verificar_direcao(direcao)
        tentativa = 0
        valor = self.entrada

        while tentativa <= max_mg:
            try:
                # Registra a tentativa para debug
                log_trade_attempt(self.par, direcao, valor, self.tempo)
                
                # Verifica se o par está disponível
                pares_abertos = self.api.get_all_open_time()
                if pares_abertos is not None:
                    log_api_response(pares_abertos, "get_all_open_time")
                    
                if pares_abertos and self.par in pares_abertos['binary'] and pares_abertos['binary'][self.par]['open']:
                    print(f"[i] Par {self.par} está disponível para negociação")
                else:
                    print(f"[❌] ERRO: Par {self.par} não está disponível para negociação")
                    return False, 0
                
                # Verifica se o tempo de expiração é válido
                exp_modes = self.api.get_all_profit()
                log_api_response(exp_modes, "get_all_profit")
                
                # Certifica-se de que estamos usando um tempo de expiração válido em minutos
                tempo_expiracao = self.tempo
                # Para expiração em minutos, use M1, M5, M15 etc
                tempo_expiracao_str = f"M{self.tempo}"
                
                # Faz a compra com timeout adequado
                print(f"[i] Tentando realizar operação: {direcao.upper()} em {self.par} com valor {valor}")
                status, id = self.api.buy(valor, self.par, direcao, tempo_expiracao)
                log_api_response({"status": status, "id": id}, "buy")
                
                if status:
                    print(f"[+] Entrada: {valor} | Direção: {direcao.upper()} | Tentativa: {tentativa}")
                    # Espere pelo resultado com timeout adequado
                    timeout = tempo_expiracao * 60 + 30  # tempo em segundos + 30s de margem
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
