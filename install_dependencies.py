import subprocess
import sys
import os

def install_package(package):
    print(f"Instalando {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def main():
    print("=== Instalando dependências para o Robô Trader ===")
    
    # Lista de pacotes para instalar
    packages = [
        "websockets",
        "asyncio",
    ]
    
    # Instala os pacotes básicos
    for package in packages:
        try:
            install_package(package)
        except Exception as e:
            print(f"Erro ao instalar {package}: {e}")
    
    # Instala IQOptionAPI do GitHub
    try:
        iqoption_github = "git+https://github.com/iqoptionapi/iqoptionapi.git"
        print(f"Instalando IQOptionAPI do GitHub...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", iqoption_github])
        print("IQOptionAPI instalado com sucesso!")
    except Exception as e:
        print(f"Erro ao instalar IQOptionAPI: {e}")
        print("\nTente instalar manualmente com o comando:")
        print(f"pip install -U {iqoption_github}")
    
    print("\n=== Instalação concluída! ===")
    print("\nPara iniciar o servidor pelo terminal do VS Code, execute:")
    print("cd backend && python bot.py")
    print("\nOu execute o comando diretamente no diretório backend:")
    print("python bot.py")
    print("\n=== Pressione ENTER para sair ===")
    input()

if __name__ == "__main__":
    main()
