/**
 * Cliente WebSocket robusto para o Robô Trader
 */

class RoboTraderClient {
  constructor(url = 'ws://localhost:6789') {
    this.url = url
    this.socket = null
    this.isConnected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 10
    this.reconnectInterval = 2000 // 2 segundos
    this.eventListeners = {
      message: [],
      connect: [],
      disconnect: [],
      error: []
    }
    this.lastPingSent = 0
    this.pingInterval = null

    // Inicializar conexão
    this.connect()
  }

  /**
   * Estabelece conexão com o servidor WebSocket
   */
  connect() {
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING)
    ) {
      console.log('WebSocket já está conectado ou conectando')
      return
    }

    console.log(`Conectando ao servidor: ${this.url}`)
    this.socket = new WebSocket(this.url)

    // Configurar handlers de eventos
    this.socket.onopen = () => this._handleOpen()
    this.socket.onmessage = event => this._handleMessage(event)
    this.socket.onclose = event => this._handleClose(event)
    this.socket.onerror = error => this._handleError(error)
  }

  /**
   * Envia dados para o servidor
   * @param {Object} data - Dados a serem enviados
   */
  send(data) {
    if (!this.isConnected) {
      console.warn('Tentativa de enviar mensagem com WebSocket desconectado')
      this._triggerEvent('error', 'WebSocket não está conectado')
      return false
    }

    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      this.socket.send(message)
      return true
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error)
      this._triggerEvent('error', `Erro ao enviar mensagem: ${error.message}`)
      return false
    }
  }

  /**
   * Registra listener para eventos
   * @param {string} event - Tipo de evento ('message', 'connect', 'disconnect', 'error')
   * @param {Function} callback - Função a ser chamada quando o evento ocorrer
   */
  on(event, callback) {
    if (this.eventListeners[event]) {
      this.eventListeners[event].push(callback)
    }
  }

  /**
   * Desconecta do servidor
   */
  disconnect() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }

    if (this.socket) {
      this.socket.close()
    }
  }

  /**
   * Solicita pares disponíveis ao servidor
   */
  requestAvailablePairs() {
    this.send({ command: 'get_available_pairs' })
  }

  // Handlers de eventos internos
  _handleOpen() {
    console.log('WebSocket conectado')
    this.isConnected = true
    this.reconnectAttempts = 0

    // Configurar ping automático a cada 20 segundos
    if (this.pingInterval) clearInterval(this.pingInterval)
    this.pingInterval = setInterval(() => this._sendPing(), 20000)

    this._triggerEvent('connect', 'Conectado ao servidor')
  }

  _handleMessage(event) {
    try {
      const data = JSON.parse(event.data)

      // Tratar heartbeats silenciosamente
      if (data.status === 'heartbeat') {
        return
      }

      // Responder a pongs silenciosamente
      if (data.status === 'pong') {
        return
      }

      this._triggerEvent('message', data)
    } catch (error) {
      console.error('Erro ao processar mensagem:', error)
      this._triggerEvent(
        'error',
        `Erro ao processar mensagem: ${error.message}`
      )
    }
  }

  _handleClose(event) {
    this.isConnected = false
    console.log(
      `WebSocket desconectado. Código: ${event.code}, Razão: ${event.reason}`
    )

    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }

    this._triggerEvent(
      'disconnect',
      `Desconectado: ${event.reason || 'Sem razão especificada'}`
    )

    // Tentar reconectar automaticamente
    this._attemptReconnect()
  }

  _handleError(error) {
    console.error('Erro de WebSocket:', error)
    this._triggerEvent('error', 'Erro de conexão')
  }

  _attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Número máximo de tentativas de reconexão atingido')
      this._triggerEvent('error', 'Falha ao reconectar após várias tentativas')
      return
    }

    this.reconnectAttempts++
    const delay =
      this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1)
    const cappedDelay = Math.min(delay, 30000) // No máximo 30 segundos

    console.log(
      `Tentativa de reconexão ${this.reconnectAttempts} em ${cappedDelay}ms`
    )
    this._triggerEvent(
      'error',
      `Tentando reconectar em ${Math.round(cappedDelay / 1000)}s...`
    )

    setTimeout(() => this.connect(), cappedDelay)
  }

  _sendPing() {
    if (this.isConnected) {
      this.lastPingSent = Date.now()
      this.send({ command: 'ping' })
    }
  }

  _triggerEvent(event, data) {
    if (this.eventListeners[event]) {
      this.eventListeners[event].forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error(
            `Erro ao executar callback para evento ${event}:`,
            error
          )
        }
      })
    }
  }
}

// Exportar a classe para uso no navegador
window.RoboTraderClient = RoboTraderClient
