import os
import sys
import webbrowser
import subprocess
import time

# Banner do robô
print("""
╔══════════════════════════════════════════════╗
║                                              ║
║           ROBÔ TRADER IQ OPTION              ║
║                                              ║
║            Inicializando...                  ║
║                                              ║
╚══════════════════════════════════════════════╝
""")

# Verificar se as dependências estão instaladas
try:
    import websockets
    import asyncio
    # Tentativa de importar a biblioteca IQOptionAPI
    try:
        from iqoptionapi.stable_api import IQ_Option
        print("✅ Todas as dependências instaladas!")
    except ImportError:
        print("⚠️ IQOptionAPI não encontrada. Instalando...")
        os.system("pip install -U git+https://github.com/iqoptionapi/iqoptionapi.git")
except ImportError as e:
    print(f"⚠️ Dependência não encontrada: {e.name}")
    print("Instalando dependências...")
    os.system("pip install -r backend/requirements.txt")

# Definir o caminho para o frontend e backend
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "index.html")
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "bot.py")

# Iniciar o servidor backend
print("\n🚀 Iniciando servidor backend...")
backend_process = subprocess.Popen([sys.executable, backend_path], 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

# Aguardar o servidor iniciar
time.sleep(2)

# Verificar se o processo está rodando
if backend_process.poll() is None:
    print("✅ Servidor backend iniciado com sucesso!")
    
    # Abrir o frontend no navegador
    print("🔗 Abrindo interface web...")
    webbrowser.open('file://' + os.path.abspath(frontend_path))
    
    print("\n✨ Robô iniciado com sucesso!")
    print("📊 Interface web aberta no navegador")
    print("\nPressione Ctrl+C para encerrar o robô\n")
    
    try:
        # Manter o script rodando e exibir saída do backend
        while True:
            output = backend_process.stdout.readline()
            if output:
                print(output.decode().strip())
            # Verificar se o processo ainda está rodando
            if backend_process.poll() is not None:
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n🛑 Encerrando o robô...")
        backend_process.terminate()
else:
    print("❌ Erro ao iniciar o servidor backend!")
    print("Verifique os logs para mais informações:")
    output, error = backend_process.communicate()
    print("\nOutput:")
    print(output.decode())
    print("\nErro:")
    print(error.decode())
