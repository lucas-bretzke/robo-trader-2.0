#!/usr/bin/env python3
"""
Script para atualizar manualmente a lista de pares disponíveis na IQ Option
"""
import sys
import os
import json
import time
import traceback
from datetime import datetime

# Adiciona o diretório raiz ao PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from iqoptionapi.stable_api import IQ_Option
except ImportError:
    print("====================================================")
    print("ERRO: Biblioteca IQOptionAPI não encontrada!")
    print("\nPara instalar, execute o comando:")
    print("pip install -U git+https://github.com/iqoptionapi/iqoptionapi.git")
    print("\nOu execute o arquivo 'install_dependencies.py' na pasta do projeto.")
    print("====================================================")
    sys.exit(1)

def salvar_pares(pares, arquivo="frontend/available_pairs.json"):
    """Salva a lista de pares em um arquivo JSON"""
    try:
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(arquivo), exist_ok=True)
        
        dados = {
            "timestamp": time.time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pairs": pares
        }
        
        with open(arquivo, "w") as f:
            json.dump(dados, f, indent=2)
            
        print(f"✅ Dados salvos em {arquivo}")
        print(f"✅ Total de {len(pares)} pares disponíveis")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {str(e)}")
        return False

def obter_pares_disponiveis(api):
    """Obtém todos os pares disponíveis de todos os mercados"""
    all_pairs = []
    
    try:
        # Obter dados básicos de todos os mercados
        print("Obtendo pares disponíveis de todos os mercados...")
        all_open_time = api.get_all_open_time()
        
        # Salvar dados brutos para análise
        with open("logs/all_open_time.json", "w") as f:
            json.dump(all_open_time, f, indent=2)
        
        # Processar cada mercado
        for market in all_open_time:
            print(f"Processando mercado: {market}")
            pares_mercado = []
            
            for pair, status in all_open_time[market].items():
                if isinstance(status, dict) and status.get("open", False):
                    pares_mercado.append(pair)
                elif isinstance(status, bool) and status:
                    pares_mercado.append(pair)
            
            print(f"- {len(pares_mercado)} pares disponíveis em {market}")
            
            # Adicionar à lista total com prefixo para mercados não binários
            for pair in pares_mercado:
                if market != "binary":
                    formatted_pair = f"{market.upper()}_{pair}"
                    if formatted_pair not in all_pairs:
                        all_pairs.append(formatted_pair)
                else:
                    if pair not in all_pairs:
                        all_pairs.append(pair)
        
        # Adicionar pares digitais
        print("Obtendo pares digitais...")
        try:
            digital_pairs = api.get_digital_underlying()
            print(f"- {len(digital_pairs)} pares digitais")
            
            for pair in digital_pairs:
                formatted = f"DIGITAL_{pair}"
                if formatted not in all_pairs:
                    all_pairs.append(formatted)
        except Exception as e:
            print(f"❌ Erro ao obter pares digitais: {str(e)}")
        
        return all_pairs
    except Exception as e:
        print(f"❌ Erro ao obter pares disponíveis: {str(e)}")
        traceback.print_exc()
        return []

def main():
    print("\n=== Atualizador de Pares IQ Option ===\n")
    
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Solicitar credenciais
    email = input("Digite seu email da IQ Option: ")
    senha = input("Digite sua senha: ")
    
    print("\nConectando à IQ Option...")
    api = IQ_Option(email, senha)
    status, reason = api.connect()
    
    if not status:
        print(f"❌ Falha na conexão: {reason}")
        sys.exit(1)
    
    print("✅ Conectado com sucesso!")
    
    # Usar conta DEMO por segurança
    api.change_balance("PRACTICE")
    print(f"📊 Saldo DEMO: {api.get_balance()}")
    
    print("\nObtendo lista de pares disponíveis...\n")
    pares = obter_pares_disponiveis(api)
    
    if not pares:
        print("❌ Nenhum par disponível encontrado")
        sys.exit(1)
    
    # Organizar pares por categorias para melhor visualização
    forex = [p for p in pares if not p.startswith("DIGITAL_") and not "OTC" in p and 
             any(curr in p for curr in ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "NZD"])]
    otc = [p for p in pares if "OTC" in p]
    digital = [p for p in pares if p.startswith("DIGITAL_")]
    outros = [p for p in pares if p not in forex and p not in otc and p not in digital]
    
    print("\n=== RESUMO DOS PARES DISPONÍVEIS ===")
    print(f"🔹 FOREX: {len(forex)} pares")
    print(f"🔹 OTC: {len(otc)} pares")
    print(f"🔹 DIGITAL: {len(digital)} pares")
    print(f"🔹 OUTROS: {len(outros)} pares")
    print(f"🔹 TOTAL: {len(pares)} pares")
    
    # Salvar em arquivo
    salvar_pares(pares)
    
    print("\n✅ Processo concluído!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro não tratado: {str(e)}")
        traceback.print_exc()
    
    input("\nPressione Enter para sair...")
