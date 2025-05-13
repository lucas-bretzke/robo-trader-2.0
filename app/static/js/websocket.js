class RobotWebSocket {
  constructor(url) {
    this.url = url
    this.socket = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 2000 // Start with 2 seconds
    this.callbacks = {
      message: [],
      open: [],
      close: [],
      error: []
    }

    this.connect()
  }

  connect() {
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING)
    ) {
      return // Already connected or connecting
    }

    console.log('Connecting to WebSocket server...')
    this.socket = new WebSocket(this.url)

    this.socket.onopen = event => {
      console.log('WebSocket connection established')
      this.reconnectAttempts = 0
      this.reconnectDelay = 2000 // Reset delay on successful connection
      this.callbacks.open.forEach(callback => callback(event))

      // Set up a ping to keep the connection alive
      this.startHeartbeat()
    }

    this.socket.onmessage = event => {
      let data
      try {
        data = JSON.parse(event.data)
        // Don't log heartbeats to avoid console spam
        if (data.type !== 'heartbeat') {
          console.log('Received:', data)
        }
      } catch (e) {
        console.log('Received raw:', event.data)
        data = event.data
      }

      // Don't trigger callbacks for heartbeat messages
      if (data.type !== 'heartbeat') {
        this.callbacks.message.forEach(callback => callback(data))
      }
    }

    this.socket.onclose = event => {
      console.log(`WebSocket connection closed: ${event.code} ${event.reason}`)
      this.stopHeartbeat()
      this.callbacks.close.forEach(callback => callback(event))

      // Attempt to reconnect unless it was a clean closure
      if (
        !event.wasClean &&
        this.reconnectAttempts < this.maxReconnectAttempts
      ) {
        this.attemptReconnect()
      }
    }

    this.socket.onerror = error => {
      console.error('WebSocket error:', error)
      this.callbacks.error.forEach(callback => callback(error))
    }
  }

  attemptReconnect() {
    this.reconnectAttempts++
    const delay =
      this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1) // Exponential backoff
    const maxDelay = 30000 // Cap at 30 seconds

    console.log(
      `Attempting to reconnect in ${delay / 1000} seconds... (Attempt ${
        this.reconnectAttempts
      }/${this.maxReconnectAttempts})`
    )

    setTimeout(() => {
      this.connect()
    }, Math.min(delay, maxDelay))
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: 'ping' }))
      }
    }, 20000) // Send a ping every 20 seconds
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
    }
  }

  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      if (typeof data === 'object') {
        data = JSON.stringify(data)
      }
      this.socket.send(data)
      return true
    } else {
      console.error('Cannot send message, socket is not open')
      return false
    }
  }

  on(event, callback) {
    if (this.callbacks[event]) {
      this.callbacks[event].push(callback)
    }
    return this // For chaining
  }

  off(event, callback) {
    if (this.callbacks[event]) {
      this.callbacks[event] = this.callbacks[event].filter(
        cb => cb !== callback
      )
    }
    return this // For chaining
  }

  close() {
    this.stopHeartbeat()
    if (this.socket) {
      this.socket.close(1000, 'Closed by client')
    }
  }
}

// Usage example:
// const ws = new RobotWebSocket("ws://localhost:8000/ws");
// ws.on('message', (data) => console.log("New message:", data));
