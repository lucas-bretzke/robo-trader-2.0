// IQ Option Robot Trader - Frontend Script

// Configuration
const API_URL = 'http://localhost:8000/api'
const WS_URL = 'ws://localhost:8000/ws'

// Global state
let selectedAssets = []
let operationHistory = []
let websocket = null
let isConnected = false
let isRunning = false
let availableAssets = {
  digital: [],
  binary: []
}

// DOM elements
document.addEventListener('DOMContentLoaded', () => {
  // Initialize the application
  init()

  // Toggle password visibility
  const togglePasswordBtn = document.getElementById('toggle-password')
  const passwordInput = document.getElementById('iq-password')

  togglePasswordBtn.addEventListener('click', function () {
    if (passwordInput.type === 'text') {
      passwordInput.type = 'password'
      togglePasswordBtn.innerHTML = '<i class="eye-closed">👁️‍🗨️</i>'
    } else {
      passwordInput.type = 'text'
      togglePasswordBtn.innerHTML = '<i class="eye-open">👁️</i>'
    }
  })
})

// Initialize the application
function init() {
  // Load saved history from local storage
  loadHistoryFromLocalStorage()

  // Set up event listeners
  setupEventListeners()
}

// Setup event listeners for all interactive elements
function setupEventListeners() {
  // Account selection
  document
    .getElementById('demo-account')
    .addEventListener('click', () => selectAccount('demo'))
  document
    .getElementById('real-account')
    .addEventListener('click', () => selectAccount('real'))

  // Login button
  document.getElementById('login-btn').addEventListener('click', login)

  // Assets search
  document
    .getElementById('asset-search')
    .addEventListener('input', filterAssets)

  // Configuration
  document.getElementById('save-config').addEventListener('click', saveConfig)

  // Bot controls
  document.getElementById('start-bot').addEventListener('click', startBot)
  document.getElementById('stop-bot').addEventListener('click', stopBot)
  document.getElementById('test-entry').addEventListener('click', async () => {
    if (!isConnected) {
      addLogEntry('Você precisa estar conectado para testar entradas', 'error')
      return
    }

    const selectedAssetsElements = document.querySelectorAll(
      '#selected-assets .asset-chip'
    )
    if (selectedAssetsElements.length === 0) {
      addLogEntry('Selecione pelo menos um ativo para testar', 'error')
      return
    }

    const selectedAsset = selectedAssetsElements[0].textContent
      .trim()
      .split(' ')[0]
    const entryAmount = parseFloat(
      document.getElementById('entry-amount').value
    )
    const expiryTime = document.getElementById('expiry-time').value

    if (isNaN(entryAmount) || entryAmount <= 0) {
      addLogEntry('Valor de entrada inválido', 'error')
      return
    }

    addLogEntry(`Executando entrada de teste em ${selectedAsset}...`, 'info')

    try {
      const response = await fetch(`${API_URL}/test-entry`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          asset: selectedAsset,
          amount: entryAmount,
          direction: 'call', // Using CALL as default test
          expiry: parseInt(expiryTime)
        })
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(
          `Servidor retornou erro ${response.status}: ${errorText}`
        )
      }

      const result = await response.json()

      if (result.success) {
        addLogEntry(
          `Entrada de teste executada: ${selectedAsset} CALL`,
          'success'
        )
      } else {
        // Handle case where result.error might be undefined
        const errorMessage = result.error || 'Erro desconhecido na entrada'
        addLogEntry(`Erro na entrada de teste: ${errorMessage}`, 'error')
      }
    } catch (error) {
      addLogEntry(`Erro ao executar teste: ${error.message}`, 'error')
    }
  })

  // History
  document
    .getElementById('clear-history')
    .addEventListener('click', clearHistory)
  document
    .getElementById('date-filter')
    .addEventListener('input', filterHistory)
  document.getElementById('clear-filter').addEventListener('click', clearFilter)
}

// Account selection handler
function selectAccount(type) {
  const demoBtn = document.getElementById('demo-account')
  const realBtn = document.getElementById('real-account')

  if (type === 'demo') {
    demoBtn.classList.add('active')
    realBtn.classList.remove('active')
  } else {
    demoBtn.classList.remove('active')
    realBtn.classList.add('active')
  }
}

// Login function
async function login() {
  try {
    const accountType = document
      .getElementById('demo-account')
      .classList.contains('active')
      ? 'PRACTICE'
      : 'REAL'

    // Get credentials from the form
    const email = document.getElementById('iq-email').value.trim()
    const password = document.getElementById('iq-password').value

    // Hide previous error messages
    document.getElementById('login-error').classList.add('hidden')

    // Validate inputs
    if (!email || !password) {
      addLogEntry('Email e senha são obrigatórios', 'error')
      document.getElementById('login-error').innerHTML =
        '<p>Por favor, preencha seu email e senha.</p>'
      document.getElementById('login-error').classList.remove('hidden')
      return
    }

    // Show loading status
    document.getElementById('login-btn').disabled = true
    const loginStatus = document.getElementById('login-status')
    loginStatus.classList.remove('hidden')

    addLogEntry(`Iniciando login com conta ${accountType}...`, 'info')

    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        account_type: accountType,
        email: email,
        password: password
      })
    })

    // Hide loading status
    document.getElementById('login-btn').disabled = false
    loginStatus.classList.add('hidden')

    const data = await response.json()

    if (response.ok) {
      isConnected = true

      // Update UI
      document.getElementById('connection-status').classList.remove('offline')
      document.getElementById('connection-status').classList.add('online')
      document.getElementById(
        'status-text'
      ).textContent = `Conectado (${accountType})`
      document.getElementById('login-section').classList.add('hidden')
      document.getElementById('main-content').classList.remove('hidden')
      document.getElementById(
        'current-balance'
      ).textContent = `R$ ${data.balance.toFixed(2)}`

      addLogEntry(
        `Login bem-sucedido! Saldo: R$ ${data.balance.toFixed(2)}`,
        'info'
      )

      // Load available assets
      loadAssets()

      // Connect to WebSocket
      connectWebSocket()
    } else {
      // Show error message
      const loginErrorElement = document.getElementById('login-error')

      if (response.status === 401) {
        loginErrorElement.innerHTML = `<p>Erro de autenticação: ${data.message}</p>
                                    <p>Verifique se seu email e senha estão corretos.</p>`
      } else {
        loginErrorElement.innerHTML = `<p>Erro no login: ${data.message}</p>`
      }

      loginErrorElement.classList.remove('hidden')
      addLogEntry(`Erro no login: ${data.message}`, 'error')
    }
  } catch (error) {
    // Hide loading status in case of error
    document.getElementById('login-btn').disabled = false
    document.getElementById('login-status').classList.add('hidden')

    // Show error message
    document.getElementById(
      'login-error'
    ).innerHTML = `<p>Erro de conexão: ${error.message}</p>`
    document.getElementById('login-error').classList.remove('hidden')

    addLogEntry(`Erro no login: ${error.message}`, 'error')
  }
}

// Load available assets from API
async function loadAssets() {
  try {
    addLogEntry('Carregando ativos disponíveis...', 'info')

    const response = await fetch(`${API_URL}/assets`)
    const data = await response.json()

    if (response.ok) {
      availableAssets = data
      renderAssetsList()
      addLogEntry(
        `${data.digital.length + data.binary.length} ativos carregados`,
        'info'
      )
    } else {
      addLogEntry(`Erro ao carregar ativos: ${data.message}`, 'error')
    }
  } catch (error) {
    addLogEntry(`Erro ao carregar ativos: ${error.message}`, 'error')
  }
}

// Render the list of available assets
function renderAssetsList() {
  const assetsList = document.getElementById('assets-list')
  const allAssets = [
    ...availableAssets.digital,
    ...availableAssets.binary
  ].sort()

  // Remove duplicates
  const uniqueAssets = [...new Set(allAssets)]

  assetsList.innerHTML = ''

  if (uniqueAssets.length === 0) {
    assetsList.innerHTML = '<p>Nenhum ativo disponível</p>'
    return
  }

  uniqueAssets.forEach(asset => {
    const assetItem = document.createElement('div')
    assetItem.className = 'asset-item'
    assetItem.textContent = asset
    assetItem.addEventListener('click', () => toggleAssetSelection(asset))
    assetsList.appendChild(assetItem)
  })
}

// Filter assets by search term
function filterAssets() {
  const searchTerm = document.getElementById('asset-search').value.toUpperCase()
  const assetItems = document.querySelectorAll('.asset-item')

  assetItems.forEach(item => {
    const assetName = item.textContent
    if (assetName.toUpperCase().indexOf(searchTerm) > -1) {
      item.style.display = ''
    } else {
      item.style.display = 'none'
    }
  })
}

// Toggle asset selection
function toggleAssetSelection(asset) {
  const index = selectedAssets.indexOf(asset)

  if (index > -1) {
    selectedAssets.splice(index, 1)
  } else {
    selectedAssets.push(asset)
  }

  renderSelectedAssets()
}

// Render the list of selected assets
function renderSelectedAssets() {
  const selectedAssetsElement = document.getElementById('selected-assets')

  if (selectedAssets.length === 0) {
    selectedAssetsElement.innerHTML = '<p>Nenhum ativo selecionado</p>'
    return
  }

  selectedAssetsElement.innerHTML = ''

  selectedAssets.forEach(asset => {
    const assetChip = document.createElement('span')
    assetChip.className = 'asset-chip'
    assetChip.innerHTML = `${asset} <span class="remove-asset" onclick="toggleAssetSelection('${asset}')">✕</span>`
    selectedAssetsElement.appendChild(assetChip)
  })
}

// Save configuration
async function saveConfig() {
  try {
    if (selectedAssets.length === 0) {
      addLogEntry('Erro: Selecione pelo menos um ativo', 'error')
      alert('Selecione pelo menos um ativo')
      return
    }

    const config = {
      assets: selectedAssets,
      candle_time: parseInt(document.getElementById('candle-time').value),
      expiration_time: parseInt(document.getElementById('expiry-time').value),
      money_management: document.getElementById('money-management').value,
      entry_amount: parseFloat(document.getElementById('entry-amount').value),
      stop_gain: parseFloat(document.getElementById('stop-gain').value),
      stop_loss: parseFloat(document.getElementById('stop-loss').value)
    }

    addLogEntry('Salvando configurações...', 'info')

    const response = await fetch(`${API_URL}/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config)
    })

    const data = await response.json()

    if (response.ok) {
      addLogEntry('Configurações salvas com sucesso!', 'info')
      alert('Configurações salvas com sucesso!')
    } else {
      addLogEntry(`Erro ao salvar configurações: ${data.message}`, 'error')
      alert(`Erro ao salvar configurações: ${data.message}`)
    }
  } catch (error) {
    addLogEntry(`Erro ao salvar configurações: ${error.message}`, 'error')
    alert(`Erro ao salvar configurações: ${error.message}`)
  }
}

// Start the trading bot
async function startBot() {
  try {
    addLogEntry('Iniciando robô...', 'info')

    const response = await fetch(`${API_URL}/start`, {
      method: 'POST'
    })

    const data = await response.json()

    if (response.ok) {
      isRunning = true
      document.getElementById('start-bot').classList.add('hidden')
      document.getElementById('stop-bot').classList.remove('hidden')
      addLogEntry('Robô iniciado com sucesso!', 'info')
    } else {
      addLogEntry(`Erro ao iniciar robô: ${data.message}`, 'error')
      alert(`Erro ao iniciar robô: ${data.message}`)
    }
  } catch (error) {
    addLogEntry(`Erro ao iniciar robô: ${error.message}`, 'error')
    alert(`Erro ao iniciar robô: ${error.message}`)
  }
}

// Stop the trading bot
async function stopBot() {
  try {
    addLogEntry('Parando robô...', 'info')

    const response = await fetch(`${API_URL}/stop`, {
      method: 'POST'
    })

    const data = await response.json()

    if (response.ok) {
      isRunning = false
      document.getElementById('start-bot').classList.remove('hidden')
      document.getElementById('stop-bot').classList.add('hidden')
      addLogEntry('Robô parado com sucesso!', 'info')
    } else {
      addLogEntry(`Erro ao parar robô: ${data.message}`, 'error')
      alert(`Erro ao parar robô: ${data.message}`)
    }
  } catch (error) {
    addLogEntry(`Erro ao parar robô: ${error.message}`, 'error')
    alert(`Erro ao parar robô: ${error.message}`)
  }
}

// Test a trade entry
async function executeTrade(asset, direction, amount, expiry) {
  try {
    const response = await fetch(`${API_URL}/execute-trade`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        asset: asset,
        amount: amount,
        direction: direction,
        expiry: expiry
      })
    })

    const result = await response.json()

    if (result.success) {
      addLogEntry(
        `Operação executada: ${asset} ${direction.toUpperCase()}`,
        'success'
      )
      addOperationToHistory(result)
      return result
    } else {
      addLogEntry(`Erro na operação: ${result.error}`, 'error')
      return null
    }
  } catch (error) {
    addLogEntry(`Erro ao executar operação: ${error.message}`, 'error')
    return null
  }
}

// Add a log entry to the logs container
function addLogEntry(message, level = 'info') {
  const logsContainer = document.getElementById('logs-container')
  const logEntry = document.createElement('div')
  logEntry.className = `log-entry log-${level}`

  const now = new Date()
  const timeString = `${now.getHours().toString().padStart(2, '0')}:${now
    .getMinutes()
    .toString()
    .padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`

  logEntry.innerHTML = `<span class="log-time">${timeString}</span> ${message}`
  logsContainer.appendChild(logEntry)

  // Auto-scroll to bottom
  logsContainer.scrollTop = logsContainer.scrollHeight
}

// Connect to WebSocket for real-time updates
function connectWebSocket() {
  if (websocket) {
    websocket.close()
  }

  websocket = new WebSocket(WS_URL)

  websocket.onopen = event => {
    addLogEntry('Conexão WebSocket estabelecida', 'info')
  }

  websocket.onmessage = event => {
    const data = JSON.parse(event.data)

    if (data.type === 'update') {
      updateDashboard(data.daily_result)
    } else if (data.type === 'operation') {
      updateDashboard(data.daily_result)
      if (data.data && data.data.id) {
        addOperationToHistory(data.data)
      }
    } else if (data.type === 'analysis') {
      addLogEntry(
        `Análise para ${data.asset}: ${
          data.signal ? data.direction.toUpperCase() : 'Sem sinal'
        }`,
        'info'
      )
    } else if (data.type === 'alert') {
      addLogEntry(data.message, 'warning')
      alert(data.message)
    }
  }

  websocket.onclose = event => {
    addLogEntry('Conexão WebSocket fechada', 'warning')

    // Try to reconnect after 5 seconds
    setTimeout(() => {
      if (isConnected) {
        connectWebSocket()
      }
    }, 5000)
  }

  websocket.onerror = error => {
    addLogEntry('Erro na conexão WebSocket', 'error')
  }

  // Keep connection alive
  setInterval(() => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send('ping')
    }
  }, 30000)
}

// Update dashboard with new data
function updateDashboard(data) {
  if (!data) return

  document.getElementById(
    'current-balance'
  ).textContent = `R$ ${data.current_balance.toFixed(2)}`
  document.getElementById('total-operations').textContent =
    data.total_operations
  document.getElementById('total-wins').textContent = data.wins
  document.getElementById('win-rate').textContent = `${data.win_rate.toFixed(
    2
  )}%`

  const profitLossElement = document.getElementById('profit-loss')
  profitLossElement.textContent = `R$ ${Math.abs(data.profit_loss).toFixed(2)}`
  profitLossElement.className = `dashboard-value ${
    data.profit_loss >= 0 ? 'win' : 'loss'
  }`

  document.getElementById(
    'max-amount'
  ).textContent = `R$ ${data.max_amount.toFixed(2)}`

  const minAmountElement = document.getElementById('min-amount')
  if (data.min_amount !== Infinity) {
    minAmountElement.textContent = `R$ ${data.min_amount.toFixed(2)}`
  } else {
    minAmountElement.textContent = `R$ 0.00`
  }

  document.getElementById(
    'max-profit'
  ).textContent = `R$ ${data.max_profit.toFixed(2)}`
  document.getElementById('max-loss').textContent = `R$ ${Math.abs(
    data.max_loss
  ).toFixed(2)}`

  // Update bot status buttons
  if (data.is_running !== isRunning) {
    isRunning = data.is_running
    if (isRunning) {
      document.getElementById('start-bot').classList.add('hidden')
      document.getElementById('stop-bot').classList.remove('hidden')
    } else {
      document.getElementById('start-bot').classList.remove('hidden')
      document.getElementById('stop-bot').classList.add('hidden')
    }
  }
}

// Add a new operation to the history
function addOperationToHistory(operation) {
  operationHistory.push(operation)

  // Update table
  renderHistoryTable()

  // Save to local storage
  saveHistoryToLocalStorage()
}

// Load operation history from local storage
function loadHistoryFromLocalStorage() {
  const savedHistory = localStorage.getItem('operationHistory')
  if (savedHistory) {
    try {
      operationHistory = JSON.parse(savedHistory)
      renderHistoryTable()
    } catch (error) {
      console.error('Error loading history from local storage:', error)
    }
  }
}

// Save operation history to local storage
function saveHistoryToLocalStorage() {
  localStorage.setItem('operationHistory', JSON.stringify(operationHistory))
}

// Render the history table
function renderHistoryTable() {
  const historyBody = document.getElementById('history-body')
  historyBody.innerHTML = ''

  if (operationHistory.length === 0) {
    const noDataRow = document.createElement('tr')
    noDataRow.innerHTML =
      '<td colspan="5" style="text-align: center;">Nenhuma operação encontrada</td>'
    historyBody.appendChild(noDataRow)
    return
  }

  // Get date filter
  const dateFilter = document.getElementById('date-filter').value

  // Filter operations by date if filter is set
  const filteredHistory = dateFilter
    ? operationHistory.filter(op => op.time.startsWith(dateFilter))
    : operationHistory

  // Sort by time (newest first)
  const sortedHistory = [...filteredHistory].reverse()

  sortedHistory.forEach(op => {
    const row = document.createElement('tr')

    // Format time
    const opDate = new Date(op.time)
    const timeFormatted = `${opDate.getDate().toString().padStart(2, '0')}/${(
      opDate.getMonth() + 1
    )
      .toString()
      .padStart(2, '0')} ${opDate
      .getHours()
      .toString()
      .padStart(2, '0')}:${opDate.getMinutes().toString().padStart(2, '0')}`

    row.innerHTML = `
            <td>${timeFormatted}</td>
            <td>${op.asset}</td>
            <td>${op.direction.toUpperCase()}</td>
            <td>R$ ${op.amount.toFixed(2)}</td>
            <td class="${op.status}">${
      op.status === 'win' ? '+' : ''
    }R$ ${Math.abs(op.result).toFixed(2)}</td>
        `

    historyBody.appendChild(row)
  })
}

// Clear operation history
async function clearHistory() {
  if (
    !confirm('Tem certeza que deseja limpar todo o histórico de operações?')
  ) {
    return
  }

  try {
    const response = await fetch(`${API_URL}/clear-history`, {
      method: 'POST'
    })

    const data = await response.json()

    if (response.ok) {
      operationHistory = []
      renderHistoryTable()

      // Clear local storage
      localStorage.removeItem('operationHistory')

      addLogEntry('Histórico limpo com sucesso', 'info')
    } else {
      addLogEntry(`Erro ao limpar histórico: ${data.message}`, 'error')
    }
  } catch (error) {
    addLogEntry(`Erro ao limpar histórico: ${error.message}`, 'error')
  }
}

// Filter history by date
function filterHistory() {
  renderHistoryTable()
}

// Clear date filter
function clearFilter() {
  document.getElementById('date-filter').value = ''
  renderHistoryTable()
}
