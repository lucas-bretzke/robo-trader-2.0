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

print("=== Diagnóstico de Pares da IQ Option ===")
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

def main():
    print("\nIniciando diagnóstico...")
    
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
    
    # Teste 1: Obter todos os pares disponíveis
    print("\n⏳ Testando get_all_open_time()...")
    try:
        result = api.get_all_open_time()
        arquivo = salvar_json(result, "all_open_time.json")
        
        # Analisar e mostrar chaves da resposta
        print(f"\nChaves na resposta: {list(result.keys())}")
        
        total_pares = 0
        for tipo in result.keys():
            if isinstance(result[tipo], dict):
                pares_abertos = [par for par, status in result[tipo].items() 
                               if isinstance(status, dict) and status.get("open", False)]
                print(f"- Tipo {tipo}: {len(pares_abertos)} pares abertos")
                total_pares += len(pares_abertos)
                
                # Mostrar alguns exemplos de pares
                if pares_abertos:
                    print(f"  Exemplos: {', '.join(pares_abertos[:5])}")
        
        print(f"\n✅ Total de pares disponíveis: {total_pares}")
    except Exception as e:
        print(f"❌ Erro ao obter pares: {e}")
        traceback.print_exc()
    
    # Teste 2: Verificar um par específico
    print("\n⏳ Testando pares específicos...")
    pares_teste = ["EURUSD", "EURUSD-OTC", "USDJPY", "BTCUSD"]
    
    for par in pares_teste:
        disponivel = False
        for tipo, pares in result.items():
            if par in pares and isinstance(pares[par], dict) and pares[par].get("open", False):
                disponivel = True
                print(f"✅ {par} está disponível no tipo {tipo}")
                break
        
        if not disponivel:
            print(f"❌ {par} não está disponível")
    
    # Teste 3: Testar suporte a diferentes tipos de contrato
    print("\n⏳ Testando tipos de contratos...")
    try:
        result = api.get_all_profit()
        salvar_json(result, "all_profit.json")
        print("✅ Informações de lucro salvas")
    except Exception as e:
        print(f"❌ Erro ao obter informações de lucro: {e}")
    
    print("\n✅ Diagnóstico concluído!")
    print(f"Resultados detalhados estão na pasta 'logs'")
    print("\nPara visualizar os pares disponíveis, abra o arquivo:")
    print(f"{arquivo}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro não tratado: {e}")
        traceback.print_exc()
    
    input("\nPressione Enter para sair...")
