import sys
import os
import json
import time
import traceback

def add_to_pythonpath():
    """Adiciona o diretório atual ao PYTHONPATH"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

add_to_pythonpath()

print("=== Verificador de Pares IQ Option ===")
print("Verificando dependências...")

try:
    from iqoptionapi.stable_api import IQ_Option
    print("✅ Biblioteca IQOptionAPI encontrada")
except ImportError:
    print("❌ Erro ao importar IQOptionAPI")
    print("Instalando biblioteca...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "git+https://github.com/iqoptionapi/iqoptionapi.git"])
        print("✅ Biblioteca instalada com sucesso")
        from iqoptionapi.stable_api import IQ_Option
    except Exception as e:
        print(f"❌ Falha ao instalar: {e}")
        sys.exit(1)

def criar_diretorio_logs():
    """Cria diretório de logs se não existir"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def salvar_json(data, nome_arquivo):
    """Salva dados como JSON"""
    log_dir = criar_diretorio_logs()
    arquivo = os.path.join(log_dir, nome_arquivo)
    
    with open(arquivo, "w") as f:
        json.dump(data, f, indent=2)
        
    print(f"✅ Dados salvos em {arquivo}")
    return arquivo

def verificar_par_disponivel(par, iq):
    """Função que verifica disponibilidade de um par"""
    # Tratamento especial para "TODOS"
    if par.upper() == "TODOS":
        print("✅ 'TODOS' é uma opção especial para monitorar todos os pares")
        return True
        
    all_open_time = iq.get_all_open_time()
    
    # Verifica em cada tipo de mercado
    for market in ["binary", "turbo", "digital"]:
        if market in all_open_time:
            if par in all_open_time[market]:
                if all_open_time[market][par]["open"]:
                    print(f"✅ Par {par} está disponível no mercado {market}")
                    return True
                else:
                    print(f"❌ Par {par} existe no mercado {market}, mas está fechado")
    
    print(f"❌ Par {par} não encontrado em nenhum mercado disponível")
    return False

def main():
    print("\nIniciando verificação de pares...")
    
    # Solicitar credenciais
    email = input("Digite seu email da IQ Option: ")
    senha = input("Digite sua senha: ")
    
    print("\n⏳ Conectando à IQ Option...")
    api = IQ_Option(email, senha)
    status, reason = api.connect()
    
    if not status:
        print(f"❌ Falha na conexão: {reason}")
        return
        
    print("✅ Conectado com sucesso!")
    print("🏦 Tipo de conta: DEMO")
    api.change_balance("PRACTICE")
    
    # Loop para verificar pares
    while True:
        print("\n=== VERIFICAÇÃO DE PARES ===")
        print("Digite o par que deseja verificar (ou 'sair' para encerrar):")
        par = input().upper()
        
        if par == "SAIR":
            break
            
        # Verifica disponibilidade do par ou do tratamento especial "TODOS"
        verificar_par_disponivel(par, api)
    
    print("\n✅ Verificação concluída!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro não tratado: {e}")
        traceback.print_exc()
    
    input("\nPressione Enter para sair...")
