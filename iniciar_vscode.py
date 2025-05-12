import os
import sys
import subprocess
import webbrowser
import time

def abrir_vs_code():
    """Abre o projeto no Visual Studio Code"""
    try:
        # Tenta abrir o VS Code com o projeto
        print("Abrindo o projeto no Visual Studio Code...")
        projeto_path = os.path.dirname(os.path.abspath(__file__))
        
        # Tenta diferentes comandos para o VS Code
        comandos = ["code", "code.cmd", "code.exe"]
        sucesso = False
        
        for cmd in comandos:
            try:
                subprocess.Popen([cmd, projeto_path])
                sucesso = True
                print("Visual Studio Code aberto com sucesso!")
                break
            except Exception:
                continue
                
        if not sucesso:
            print("Não foi possível abrir automaticamente o VS Code.")
            print(f"Por favor, abra o VS Code manualmente e abra a pasta: {projeto_path}")
    except Exception as e:
        print(f"Erro ao abrir o VS Code: {e}")

def mostrar_instrucoes():
    """Mostra instruções para iniciar o servidor no terminal do VS Code"""
    print("\n=== INSTRUÇÕES PARA INICIAR O SERVIDOR PELO TERMINAL DO VS CODE ===\n")
    print("1. No VS Code, abra um terminal (Menu Terminal -> Novo Terminal)")
    print("2. Navegue até a pasta backend com o comando:")
    print("   cd backend")
    print("3. Execute o servidor com o comando:")
    print("   python bot.py")
    print("\n4. Para abrir a interface web, digite no navegador:")
    print("   file:///c:/Users/lucas/OneDrive/Área%20de%20Trabalho/roboTrader2/frontend/index.html")
    print("\n=== ATENÇÃO ===")
    print("Deixe o terminal do VS Code rodando enquanto estiver usando o robô!")

def abrir_navegador():
    """Abre a interface web no navegador padrão"""
    try:
        # Caminho para a interface web
        caminho_frontend = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                       "frontend", "index.html")
        
        # Converte para URL de arquivo
        url_frontend = f"file:///{caminho_frontend.replace(os.sep, '/')}"
        
        print(f"\nDeseja abrir a interface web no navegador? (S/N)")
        resposta = input().strip().lower()
        
        if resposta == 's':
            print("Abrindo interface web no navegador padrão...")
            webbrowser.open(url_frontend)
    except Exception as e:
        print(f"Erro ao abrir o navegador: {e}")

def instalar_dependencias():
    """Executa o script de instalação de dependências"""
    try:
        print("Verificando dependências necessárias...")
        caminho_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                     "install_dependencies.py")
        
        subprocess.check_call([sys.executable, caminho_script])
    except Exception as e:
        print(f"Erro ao instalar dependências: {e}")

def main():
    print("\n=== ROBÔ TRADER IQ OPTION - INICIALIZAÇÃO PELO VS CODE ===\n")
    
    # Instala dependências
    instalar_dependencias()
    
    # Abre o VS Code
    abrir_vs_code()
    
    # Mostra instruções
    mostrar_instrucoes()
    
    # Abre o navegador
    abrir_navegador()
    
    print("\nProcesso de inicialização concluído.")
    print("Pressione ENTER para sair...")
    input()

if __name__ == "__main__":
    main()
