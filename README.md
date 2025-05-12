# Robô Trader IQ Option

Este é um sistema automatizado para operações na IQ Option.

## Opções para Iniciar o Servidor

Há várias formas de iniciar o servidor do Robô Trader:

### Opção 1: Iniciar pelo VS Code (Recomendado para desenvolvedores)

1. Execute o arquivo `iniciar_vscode.py` para abrir o projeto no VS Code
2. No VS Code, abra um terminal (Menu Terminal -> Novo Terminal)
3. Digite os comandos:
   ```
   cd backend
   python bot.py
   ```
4. Mantenha o terminal aberto enquanto estiver usando o robô
5. Em um navegador, abra o arquivo `frontend/index.html`

### Opção 2: Iniciar diretamente (Método simples)

1. Execute o arquivo `iniciar_servidor.bat` com duplo clique
2. Em um navegador, abra o arquivo `frontend/index.html`

### Opção 3: Usar interface web completa

1. Abra `abrir.html` em seu navegador
2. Siga as instruções na interface

## Problemas Comuns

Se encontrar problemas para conectar:

1. Verifique se todas as dependências estão instaladas executando `install_dependencies.py`
2. Certifique-se de que o servidor backend está rodando antes de abrir a interface
3. Verifique se a porta 6789 não está sendo bloqueada pelo firewall

## Notificações de Status

A interface mostrará o status da conexão com o servidor. Se aparecer "Desconectado",
verifique se o servidor backend está em execução.
