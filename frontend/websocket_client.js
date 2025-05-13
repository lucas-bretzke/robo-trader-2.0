/**
 * Cliente WebSocket robusto para o Robô Trader
 */

class RoboTraderClient {
  constructor(url = 'ws://localhost:6789') {
    this.url = url
    this.socket = null
    this.isConnected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 100 // Aumentado para ser praticamente infinito
    this.reconnectInterval = 2000 // 2 segundos
    this.eventListeners = {
      message: [],
      connect: [],
      disconnect: [],
      error: []
    }
    this.lastPingSent = 0
    this.lastPongReceived = 0
    this.pingInterval = null
    this.pingTimeout = null
    this.forcedDisconnect = false
    this.connectionCheckInterval = null

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

    // Se foi desconectado manualmente, não tente reconectar
    if (this.forcedDisconnect) {
      console.log('Conexão não iniciada porque foi desconectada manualmente')
      return
    }

    console.log(`Conectando ao servidor: ${this.url}`)

    try {
      this.socket = new WebSocket(this.url)

      // Configurar handlers de eventos
      this.socket.onopen = () => this._handleOpen()
      this.socket.onmessage = event => this._handleMessage(event)
      this.socket.onclose = event => this._handleClose(event)
      this.socket.onerror = error => this._handleError(error)
    } catch (error) {
      console.error('Erro ao criar WebSocket:', error)
      this._handleError(error)
    }
  }

  /**
   * Envia dados para o servidor
   * @param {Object} data - Dados a serem enviados
   */
  send(data) {
    if (!this.isConnected) {
      console.warn('Tentativa de enviar mensagem com WebSocket desconectado')
      this._triggerEvent('error', 'WebSocket não está conectado')

      // Tentar reconectar automaticamente
      this._attemptReconnect()

      return false
    }

    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      this.socket.send(message)
      return true
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error)
      this._triggerEvent('error', `Erro ao enviar mensagem: ${error.message}`)

      // Se falhar ao enviar, possivelmente a conexão foi interrompida
      this.isConnected = false
      this._attemptReconnect()

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
    return this // Para encadeamento
  }

  /**
   * Desconecta do servidor de forma controlada
   */
  disconnect() {
    this.forcedDisconnect = true

    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }

    if (this.pingTimeout) {
      clearTimeout(this.pingTimeout)
      this.pingTimeout = null
    }

    if (this.connectionCheckInterval) {
      clearInterval(this.connectionCheckInterval)
      this.connectionCheckInterval = null
    }

    if (this.socket) {
      try {
        // Código 1000 indica fechamento normal
        this.socket.close(1000, 'Desconexão manual pelo usuário')
      } catch (error) {
        console.error('Erro ao fechar WebSocket:', error)
      }
    }

    this.isConnected = false
    this._triggerEvent('disconnect', 'Desconectado pelo usuário')
  }

  /**
   * Solicita pares disponíveis ao servidor
   */
  requestAvailablePairs() {
    this.send({
      command: 'get_available_pairs',
      detailed: true,
      include_all_markets: true
    })
  }

  /**
   * Verifica a disponibilidade de um par específico
   * @param {string} pair - Par a ser verificado
   */
  checkPairAvailability(pair) {
    this.send({ command: 'check_pair_availability', pair: pair })
  }

  /**
   * Solicita diagnostico detalhado de um par específico
   * @param {string} pair - Par a ser diagnosticado
   */
  requestPairDiagnostic(pair) {
    this.send({ command: 'diagnose_pair', pair: pair })
  }

  /**
   * Verifica status da conexão e reconecta se necessário
   */
  checkConnection() {
    if (!this.isConnected && !this.forcedDisconnect) {
      console.log(
        'Verificação de conexão detectou desconexão, tentando reconectar...'
      )
      this._attemptReconnect()
    }
  }

  // Handlers de eventos internos
  _handleOpen() {
    console.log('WebSocket conectado')
    this.isConnected = true
    this.reconnectAttempts = 0
    this.forcedDisconnect = false

    // Configurar ping automático a cada 15 segundos (reduzido de 20)
    if (this.pingInterval) clearInterval(this.pingInterval)
    this.pingInterval = setInterval(() => this._sendPing(), 15000)

    // Verificação de conexão a cada 30 segundos
    if (this.connectionCheckInterval)
      clearInterval(this.connectionCheckInterval)
    this.connectionCheckInterval = setInterval(
      () => this.checkConnection(),
      30000
    )

    this._triggerEvent('connect', 'Conectado ao servidor')
  }

  _handleMessage(event) {
    try {
      const data = JSON.parse(event.data)

      // Tratar heartbeats silenciosamente
      if (data.status === 'heartbeat') {
        this.lastPongReceived = Date.now()
        return
      }

      // Responder a pongs silenciosamente
      if (data.status === 'pong') {
        this.lastPongReceived = Date.now()
        // Limpar o timeout de ping quando receber resposta
        if (this.pingTimeout) {
          clearTimeout(this.pingTimeout)
          this.pingTimeout = null
        }
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
    if (this.isConnected) {
      this.isConnected = false
      console.log(
        `WebSocket desconectado. Código: ${event.code}, Razão: ${
          event.reason || 'Não especificada'
        }`
      )

      if (this.pingInterval) {
        clearInterval(this.pingInterval)
        this.pingInterval = null
      }

      if (this.pingTimeout) {
        clearTimeout(this.pingTimeout)
        this.pingTimeout = null
      }

      this._triggerEvent(
        'disconnect',
        `Desconectado: ${event.reason || 'Sem razão especificada'} (código: ${
          event.code
        })`
      )

      // Não tentar reconectar se foi uma desconexão manual ou código normal (1000)
      if (!this.forcedDisconnect && event.code !== 1000) {
        this._attemptReconnect()
      }
    }
  }

  _handleError(error) {
    console.error('Erro de WebSocket:', error)
    this._triggerEvent('error', 'Erro de conexão')

    // Marcar como desconectado em caso de erro
    this.isConnected = false

    // Tentar reconectar após erro, se não foi desconexão manual
    if (!this.forcedDisconnect) {
      this._attemptReconnect()
    }
  }

  _attemptReconnect() {
    if (this.forcedDisconnect) {
      console.log('Não tentando reconectar pois foi desconectado manualmente')
      return
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Número máximo de tentativas de reconexão atingido')
      this._triggerEvent('error', 'Falha ao reconectar após várias tentativas')
      return
    }

    this.reconnectAttempts++
    const delay =
      this.reconnectInterval *
      Math.pow(1.5, Math.min(10, this.reconnectAttempts - 1))
    const cappedDelay = Math.min(delay, 30000) // No máximo 30 segundos

    console.log(
      `Tentativa de reconexão ${this.reconnectAttempts} em ${cappedDelay}ms`
    )
    this._triggerEvent(
      'error',
      `Tentando reconectar em ${Math.round(
        cappedDelay / 1000
      )}s... (tentativa ${this.reconnectAttempts})`
    )

    // Limpar quaisquer temporizadores existentes
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }

    if (this.pingTimeout) {
      clearTimeout(this.pingTimeout)
      this.pingTimeout = null
    }

    setTimeout(() => this.connect(), cappedDelay)
  }

  _sendPing() {
    if (this.isConnected) {
      try {
        this.lastPingSent = Date.now()
        this.send({ command: 'ping' })

        // Definir um timeout para verificar se recebemos resposta
        if (this.pingTimeout) {
          clearTimeout(this.pingTimeout)
        }

        // Se não receber resposta em 10 segundos, considerar desconectado
        this.pingTimeout = setTimeout(() => {
          console.warn('Timeout de ping atingido, considerando desconectado')
          this.isConnected = false
          this._triggerEvent('error', 'Conexão perdida (timeout de ping)')

          // Forçar fechamento do socket atual
          try {
            if (this.socket) {
              this.socket.close()
              this.socket = null
            }
          } catch (e) {
            console.error('Erro ao fechar socket após timeout:', e)
          }

          // Iniciar processo de reconexão
          this._attemptReconnect()
        }, 10000)
      } catch (error) {
        console.error('Erro ao enviar ping:', error)
        // Se falhar, marcar como desconectado e tentar reconectar
        this.isConnected = false
        this._attemptReconnect()
      }
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
