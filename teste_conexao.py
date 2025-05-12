import sys
import time
import json
import traceback
import os

try:
    print("Tentando importar a biblioteca IQOptionAPI...")
    from iqoptionapi.stable_api import IQ_Option
    print("✅ Biblioteca importada com sucesso!")
except ImportError as e:
    print("❌ Erro ao importar a biblioteca IQOptionAPI.")
    print(f"Detalhes: {str(e)}")
    print("\nPara instalar a biblioteca, execute:")
    print("pip install -U git+https://github.com/iqoptionapi/iqoptionapi.git")
    input("Pressione Enter para sair...")
    sys.exit(1)

def salvar_log(mensagem, tipo="INFO"):
    """Salva mensagem em arquivo de log"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "teste_conexao.log")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] [{tipo}] {mensagem}\n")

def salvar_json(data, nome_arquivo):
    """Salva dados como JSON"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    json_file = os.path.join(log_dir, nome_arquivo)
    
    with open(json_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Dados salvos em {json_file}")

def main():
    print("\n=== Teste de Conexão com a IQ Option ===\n")
    
    # Solicita credenciais
    email = input("Digite seu email da IQ Option: ")
    senha = input("Digite sua senha: ")
    
    try:
        print("\nConectando à IQ Option...")
        iq = IQ_Option(email, senha)
        status, reason = iq.connect()
        
        if status:
            print("✅ Conexão estabelecida com sucesso!")
            salvar_log("Conexão estabelecida com sucesso")
            
            # Verifica o tipo de conta
            print("\nVerificando tipos de conta disponíveis...")
            iq.change_balance("PRACTICE")  # Muda para conta demo por segurança
            saldo = iq.get_balance()
            print(f"Saldo da conta DEMO: {saldo}")
            salvar_log(f"Saldo da conta DEMO: {saldo}")
            
            # Verifica pares disponíveis
            print("\nVerificando pares disponíveis...")
            pares_abertos = iq.get_all_open_time()
            
            # Salva os pares disponíveis em um arquivo
            salvar_json(pares_abertos, "pares_disponiveis.json")
            
            # Mostra os pares abertos para operação
            print("\nPares binários disponíveis para operação:")
            pares_disponiveis = []
            
            for par, status in pares_abertos["binary"].items():
                if status["open"]:
                    pares_disponiveis.append(par)
            
            for par in sorted(pares_disponiveis):
                print(f"- {par}")
            
            # Teste de compra para um par específico
            print("\nDeseja testar uma operação de compra? (s/n)")
            resposta = input().lower()
            
            if resposta == 's':
                print("\nEscolha um par da lista acima:")
                par = input().upper()
                
                if par in pares_disponiveis:
                    print(f"Testando compra para {par}...")
                    
                    try:
                        # Usando valores mínimos para teste
                        status, id = iq.buy(1, par, "call", 1)
                        
                        if status:
                            print(f"✅ Ordem enviada com sucesso! ID: {id}")
                            salvar_log(f"Ordem enviada com sucesso para {par}. ID: {id}", "TRADE")
                            
                            print("Aguardando resultado...")
                            # Aguarda resultado
                            for _ in range(70):  # Espera até 70 segundos
                                resultado = iq.check_win_v4(id)
                                if resultado != None and resultado != 0:
                                    break
                                time.sleep(1)
                                print(".", end="", flush=True)
                            
                            print(f"\nResultado: {resultado}")
                            salvar_log(f"Resultado da operação {id}: {resultado}", "RESULT")
                        else:
                            print("❌ Falha ao enviar ordem")
                            salvar_log(f"Falha ao enviar ordem para {par}", "ERROR")
                    
                    except Exception as e:
                        print(f"❌ Erro durante operação: {str(e)}")
                        traceback.print_exc()
                        salvar_log(f"Erro durante operação: {str(e)}", "ERROR")
                else:
                    print(f"❌ Par {par} não está na lista de pares disponíveis")
            
            print("\nTeste de conexão concluído!")
        else:
            print(f"❌ Falha na conexão: {reason}")
            salvar_log(f"Falha na conexão: {reason}", "ERROR")
    
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        traceback.print_exc()
        salvar_log(f"Erro: {str(e)}", "ERROR")
    
    print("\nOs resultados foram salvos na pasta 'logs'")
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()
