// Adicione manipuladores de eventos para detectar desconexões
const socket = new WebSocket(wsUrl)

socket.onopen = function (event) {
  console.log('Conexão WebSocket estabelecida')

  // Adicione um mecanismo de ping-pong para manter a conexão viva
  setInterval(() => {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'ping' }))
    }
  }, 15000) // Envie ping a cada 15 segundos
}

socket.onclose = function (event) {
  console.log(
    'Conexão WebSocket fechada com código:',
    event.code,
    'Razão:',
    event.reason
  )
  // Implemente reconexão automática se necessário
  setTimeout(() => {
    console.log('Tentando reconectar...')
    // Lógica de reconexão aqui
  }, 3000)
}

socket.onerror = function (error) {
  console.error('Erro na conexão WebSocket:', error)
}

socket.onmessage = function (event) {
  const data = JSON.parse(event.data)

  // Responda a mensagens de ping do servidor
  if (data.type === 'ping') {
    socket.send(JSON.stringify({ type: 'pong' }))
    return
  }

  // Tratamento normal das mensagens
  console.log('Mensagem recebida:', data)
}
