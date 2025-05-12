# Solução de Problemas do Robô Trader

## Problemas Comuns ao Iniciar o Robô

### 1. Erro "No module named 'iqoptionapi.stable_api'"

Este erro ocorre quando a biblioteca IQOptionAPI não está instalada corretamente.

**Solução:**

```
pip install -U git+https://github.com/iqoptionapi/iqoptionapi.git
```

### 2. Erro de conexão com o WebSocket

Se você receber erros de WebSocket no frontend:

**Solução:**

- Verifique se o servidor Python está rodando (backend/bot.py)
- Verifique se está usando "ws://localhost:6789" como URL no cliente WebSocket

### 3. Erro ao fazer login na IQ Option

**Solução:**

- Verifique suas credenciais
- Confirme se sua conta IQ Option está ativa
- Verifique sua conexão com a internet

## Como executar corretamente o robô:

1. Abra um terminal e navegue até a pasta do projeto:

   ```
   cd "C:\Users\lucas\OneDrive\Área de Trabalho\roboTrader2"
   ```

2. Instale as dependências:

   ```
   pip install -r backend/requirements.txt
   ```

3. Inicie o servidor backend:

   ```
   python backend/bot.py
   ```

4. Abra o arquivo frontend/index.html em seu navegador

## Se continuar enfrentando problemas:

- Verifique se Python 3.7+ está instalado
- Atualize pip: `pip install --upgrade pip`
- Instale as dependências separadamente:
  ```
  pip install websockets
  pip install asyncio
  pip install git+https://github.com/iqoptionapi/iqoptionapi.git
  ```
