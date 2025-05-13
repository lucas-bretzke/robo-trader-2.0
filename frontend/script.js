let roboLigado = false
let websocketClient = null
let pairCheckInterval = null // Intervalo para verificação de pares
let unavailablePairsSet = new Set() // Conjunto para armazenar pares indisponíveis
let lastCommunication = Date.now() // Timestamp da última comunicação

// Função para atualizar a interface do status do robô
function atualizarStatusRobo(ligado) {
  roboLigado = ligado
  const statusText = document.getElementById('status-text')
  const statusSwitch = document.getElementById('robot-status-switch')

  if (ligado) {
    statusText.textContent = 'Robô: LIGADO'
    statusText.className = 'status-text active'
    statusSwitch.checked = true
  } else {
    statusText.textContent = 'Robô: DESLIGADO'
    statusText.className = 'status-text inactive'
    statusSwitch.checked = false
  }
}

// Função para alternar o status do robô pelo switch
function toggleRobo() {
  const statusSwitch = document.getElementById('robot-status-switch')
  if (statusSwitch.checked) {
    roboLigado = true
    atualizarStatusRobo(true)
    logar('🤖 Ligando robô...')

    // Verifica se o par selecionado está disponível
    const selectedPair = document.getElementById('par').value
    if (selectedPair !== 'TODOS' && unavailablePairsSet.has(selectedPair)) {
      logar(
        `⚠️ AVISO: O par ${selectedPair} não está disponível para negociação!`
      )
      logar(
        'Escolha outro par ou use a opção "TODOS" para operação automática.'
      )
      flashElement(document.getElementById('par'))
      return
    }

    if (!websocketClient || !websocketClient.isConnected) {
      connectWebSocket()
    } else {
      enviarConfiguracao()
    }
  } else {
    roboLigado = false
    atualizarStatusRobo(false)
    logar('⏹️ Robô desligado.')

    if (websocketClient && websocketClient.isConnected) {
      websocketClient.send({ ligado: false })
    }

    // Limpa o intervalo de verificação quando o robô for desligado
    if (pairCheckInterval) {
      clearInterval(pairCheckInterval)
      pairCheckInterval = null
    }
  }
}

function logar(msg) {
  const log = document.getElementById('log')
  const timestamp = new Date().toLocaleTimeString()
  log.innerHTML += `<span style="color:#888">[${timestamp}]</span> ${msg}<br>`
  log.scrollTop = log.scrollHeight
}

function limparLog() {
  document.getElementById('log').innerHTML = ''
}

function updateConnectionStatus(status, color) {
  const statusEl = document.getElementById('connection-status')
  statusEl.textContent = `Estado da conexão: ${status}`
  statusEl.style.color = color
}

async function loadPairsFromFile() {
  try {
    const response = await fetch('available_pairs.json')
    if (response.ok) {
      const data = await response.json()
      logar(
        `Carregados ${data.pairs.length} pares do arquivo (atualizado em ${data.datetime})`
      )
      updatePairsList(data.pairs)
      return true
    }
  } catch (e) {
    console.error('Erro ao carregar pares do arquivo:', e)
  }
  return false
}

function updatePairsList(pairs) {
  const parSelect = document.getElementById('par')
  const currentValue = parSelect.value

  // Sempre mantém a opção TODOS
  parSelect.innerHTML =
    '<option value="TODOS">TODOS - Monitorar todos os pares</option>'

  if (pairs && pairs.length) {
    // Agrupa os pares por categorias
    const fxPairs = pairs.filter(
      p =>
        !p.includes('OTC') &&
        !p.includes('DIGITAL_') &&
        (p.includes('USD') ||
          p.includes('EUR') ||
          p.includes('GBP') ||
          p.includes('JPY'))
    )
    const otcPairs = pairs.filter(p => p.includes('OTC'))
    const digitalPairs = pairs.filter(p => p.includes('DIGITAL_'))
    const cryptoPairs = pairs.filter(
      p =>
        !p.includes('DIGITAL_') &&
        (p.includes('CRYPTO') || p.includes('BTC') || p.includes('ETH'))
    )
    const stockPairs = pairs.filter(
      p =>
        !fxPairs.includes(p) &&
        !otcPairs.includes(p) &&
        !cryptoPairs.includes(p) &&
        !digitalPairs.includes(p)
    )

    // Adiciona categorias com pares
    if (fxPairs.length) {
      parSelect.innerHTML +=
        '<option class="pair-category" disabled>--- FOREX ---</option>'
      fxPairs.forEach(pair => {
        parSelect.innerHTML += `<option value="${pair}">${pair}</option>`
      })
    }

    if (otcPairs.length) {
      parSelect.innerHTML +=
        '<option class="pair-category" disabled>--- OTC ---</option>'
      otcPairs.forEach(pair => {
        parSelect.innerHTML += `<option value="${pair}">${pair}</option>`
      })
    }

    if (digitalPairs.length) {
      parSelect.innerHTML +=
        '<option class="pair-category" disabled>--- DIGITAL ---</option>'
      digitalPairs.forEach(pair => {
        // Mostrar nome mais amigável para pares digitais
        const displayName = pair.replace('DIGITAL_', 'D_')
        parSelect.innerHTML += `<option value="${pair}">${displayName}</option>`
      })
    }

    if (cryptoPairs.length) {
      parSelect.innerHTML +=
        '<option class="pair-category" disabled>--- CRYPTO ---</option>'
      cryptoPairs.forEach(pair => {
        parSelect.innerHTML += `<option value="${pair}">${pair}</option>`
      })
    }

    if (stockPairs.length) {
      parSelect.innerHTML +=
        '<option class="pair-category" disabled>--- OUTROS ---</option>'
      stockPairs.forEach(pair => {
        parSelect.innerHTML += `<option value="${pair}">${pair}</option>`
      })
    }

    document.getElementById('pair-count').textContent = `${
      pairs.length - 1
    } pares disponíveis` // -1 para desconsiderar "TODOS"
  } else {
    document.getElementById('pair-count').textContent = '0 pares disponíveis'
    logar('⚠️ Nenhum par de moeda disponível recebido do servidor')
  }

  try {
    parSelect.value = currentValue
  } catch (e) {
    parSelect.value = 'TODOS'
  }
}

function requestAvailablePairs() {
  if (websocketClient && websocketClient.isConnected) {
    document.getElementById('refresh-pairs').parentNode.classList.add('loading')

    // Solicitar modo detalhado de pares (pede todos os mercados disponíveis)
    websocketClient.send({
      command: 'get_available_pairs',
      detailed: true,
      include_all_markets: true
    })

    logar('🔄 Solicitando lista completa de pares disponíveis...')
  } else {
    logar('⚠️ Não é possível atualizar pares: servidor desconectado')
    document
      .getElementById('refresh-pairs')
      .parentNode.classList.remove('loading')

    // Tenta carregar do arquivo quando offline
    loadPairsFromFile()
  }
}

// Adicionar função para diagnosticar um par específico
function diagnosePair(pair) {
  if (websocketClient && websocketClient.isConnected) {
    logar(`🔍 Solicitando diagnóstico detalhado para o par ${pair}...`)
    websocketClient.requestPairDiagnostic(pair)
  } else {
    logar('⚠️ Não é possível diagnosticar par: servidor desconectado')
  }
}

function connectWebSocket() {
  try {
    updateConnectionStatus('Conectando...', '#ff9800')

    // Usar a classe RoboTraderClient em vez de WebSocket diretamente
    websocketClient = new RoboTraderClient('ws://localhost:6789')

    // Registrar event listeners
    websocketClient.on('connect', function () {
      logar('✅ Conectado ao servidor com sucesso!')
      updateConnectionStatus('Conectado', '#4CAF50')

      // Solicita pares imediatamente após conectar
      setTimeout(() => requestAvailablePairs(), 500)

      if (roboLigado) {
        enviarConfiguracao()
      }
    })

    websocketClient.on('message', function (data) {
      // Sincronizar o status com o servidor, se esta informação estiver presente
      if (data.robo_status !== undefined) {
        atualizarStatusRobo(data.robo_status)
      }

      try {
        if (data.status === 'pairs_list' && data.pairs) {
          if (data.pairs.length > 0) {
            updatePairsList(data.pairs)
            document
              .getElementById('refresh-pairs')
              .parentNode.classList.remove('loading')
            logar(
              `✅ Lista de pares atualizada: ${data.pairs.length} pares disponíveis`
            )
          } else {
            document
              .getElementById('refresh-pairs')
              .parentNode.classList.remove('loading')
            logar('⚠️ Servidor retornou 0 pares disponíveis')
            // Tenta carregar de backup
            loadPairsFromFile()
          }
        } else if (data.status === 'test_entry_result') {
          // Handle test entry response
          if (data.success) {
            logar(`✅ Entrada teste realizada com sucesso: ${data.msg}`)
          } else {
            logar(`❌ Falha na entrada teste: ${data.msg}`)
          }
        } else if (data.status === 'error') {
          document
            .getElementById('refresh-pairs')
            .parentNode.classList.remove('loading')
          logar(`❌ Erro do servidor: ${data.msg}`)
        } else if (data.status === 'pair_availability') {
          // Atualizar informação de disponibilidade do par
          if (data.pair && data.available !== undefined) {
            if (data.available) {
              logar(`✅ Par ${data.pair} está disponível para negociação`)
              unavailablePairsSet.delete(data.pair)
            } else {
              logar(`⚠️ Par ${data.pair} não está disponível para negociação`)
              unavailablePairsSet.add(data.pair)
            }
          }
        } else if (data.msg) {
          logar(data.msg)
        }
      } catch (e) {
        logar(`❌ Erro ao processar resposta: ${e.message}`)
        console.error('Erro ao processar mensagem:', e, data)
      }
    })

    websocketClient.on('disconnect', function (reason) {
      updateConnectionStatus('Desconectado', '#f44336')
      logar(`Conexão fechada: ${reason}`)
    })

    websocketClient.on('error', function (error) {
      logar(`❌ Erro na conexão: ${error}`)
    })
  } catch (err) {
    logar(`❌ Erro ao criar conexão WebSocket: ${err.message}`)
    console.error(err)
    updateConnectionStatus('Falha na conexão', '#f44336')
  }
}

function enviarConfiguracao() {
  if (websocketClient && websocketClient.isConnected) {
    const config = {
      ligado: roboLigado,
      valor: parseFloat(document.getElementById('valor').value),
      multiplicador: parseFloat(document.getElementById('multiplicador').value),
      max_mg: parseInt(document.getElementById('max_mg').value),
      tempo: parseInt(document.getElementById('tempo').value),
      par: document.getElementById('par').value,
      martingale: document.getElementById('usar_mg').value === 'true',
      tipo_conta: document.getElementById('tipo_conta').value
    }

    websocketClient.send(config)
    logar(`📤 Configuração enviada ao servidor`)
  } else {
    logar('❌ Não foi possível enviar a configuração. Servidor desconectado.')
    // Tentar reconectar automaticamente
    connectWebSocket()
  }
}

// Função para obter pares disponíveis para testes
function getAvailablePairs() {
  const parSelect = document.getElementById('par')
  const options = Array.from(parSelect.options)

  // Filtrar apenas opções que são pares reais (não categorias ou TODOS)
  return options
    .filter(
      option =>
        option.value !== 'TODOS' && !option.classList.contains('pair-category')
    )
    .map(option => option.value)
}

// Função para piscar elementos
function flashElement(element) {
  const originalBg = element.style.backgroundColor
  element.style.backgroundColor = '#ffcccc'
  setTimeout(() => {
    element.style.backgroundColor = originalBg
  }, 1500)
}

// Função para fazer uma entrada teste
function testarEntrada() {
  if (!websocketClient || !websocketClient.isConnected) {
    logar('❌ Não é possível testar entrada: servidor desconectado')
    return
  }

  const tipoContaSelecionada = document.getElementById('tipo_conta').value
  if (tipoContaSelecionada === 'REAL') {
    if (
      !confirm(
        'ATENÇÃO: Você está usando uma conta REAL! Deseja realmente fazer uma entrada de teste?'
      )
    ) {
      logar('⚠️ Teste de entrada em conta real cancelado pelo usuário')
      return
    }
  }

  // Verificar se existem pares disponíveis
  const availablePairs = getAvailablePairs()
  if (availablePairs.length === 0) {
    logar(
      '❌ Não há pares disponíveis para teste. Tente recarregar a lista de pares.'
    )
    flashElement(document.getElementById('refresh-pairs'))
    return
  }

  const parSelecionado = document.getElementById('par').value
  let parParaTeste = parSelecionado

  if (parSelecionado === 'TODOS') {
    // Se selecionou TODOS, escolher um par disponível aleatoriamente
    const randomIndex = Math.floor(Math.random() * availablePairs.length)
    parParaTeste = availablePairs[randomIndex]
    logar(`⏳ Selecionando aleatoriamente o par ${parParaTeste} para teste...`)
  } else {
    // Verificar se o par específico escolhido está disponível
    if (unavailablePairsSet.has(parSelecionado)) {
      logar(`⚠️ O par ${parSelecionado} não está disponível para negociação!`)
      logar(`🔍 Solicitando diagnóstico para o par ${parSelecionado}...`)
      diagnosePair(parSelecionado)

      // Oferecer para escolher um par aleatório disponível
      const randomPair =
        availablePairs[Math.floor(Math.random() * availablePairs.length)]
      if (!confirm(`Deseja tentar com ${randomPair} em vez disso?`)) {
        return
      }
      parParaTeste = randomPair
      logar(`⏳ Usando par alternativo ${parParaTeste} para teste...`)
    } else {
      logar(`⏳ Solicitando entrada teste no par ${parParaTeste}...`)
    }
  }

  // Configuração para entrada teste
  const testConfig = {
    command: 'test_entry',
    valor: parseFloat(document.getElementById('valor').value),
    tempo: parseInt(document.getElementById('tempo').value),
    par: parParaTeste, // Usar o par escolhido ou aleatório, nunca TODOS
    tipo_conta: tipoContaSelecionada
  }

  websocketClient.send(testConfig)
  logar('📤 Requisição de entrada teste enviada')
}

// Setup inicial e event listeners
window.addEventListener('load', function () {
  logar('Bem-vindo ao Robô Trader IQ Option')
  logar('Para começar, ative o interruptor "Robô: DESLIGADO"')

  // Inicializa o status do robô (desligado por padrão)
  atualizarStatusRobo(false)

  // Event listener para tipo de conta
  document.getElementById('tipo_conta').addEventListener('change', function () {
    const warning = document.getElementById('account-warning')
    if (this.value === 'REAL') {
      warning.style.display = 'inline-block'
    } else {
      warning.style.display = 'none'
    }
  })

  // Event listener para o botão de refresh dos pares
  document
    .getElementById('refresh-pairs')
    .addEventListener('click', requestAvailablePairs)

  // Event listener para o botão de limpar log
  document.getElementById('clear-log').addEventListener('click', limparLog)

  // Event listener para o botão de testar entrada
  document
    .getElementById('test-entry-btn')
    .addEventListener('click', testarEntrada)

  setTimeout(connectWebSocket, 1000)

  setTimeout(() => {
    if (websocketClient && websocketClient.isConnected) {
      requestAvailablePairs()
    }
  }, 2000)

  // Tenta carregar pares do arquivo disponível
  loadPairsFromFile().then(loaded => {
    if (!loaded) {
      // Se não conseguir carregar do arquivo, aguarda conexão com o servidor
      logar(
        'Aguardando conexão com o servidor para carregar pares disponíveis...'
      )
    }
  })
})

// Adiciona evento para verificar disponibilidade ao mudar o par
document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('par').addEventListener('change', function () {
    const selectedPair = this.value
    if (
      selectedPair !== 'TODOS' &&
      websocketClient &&
      websocketClient.isConnected
    ) {
      // Verifica imediatamente o novo par selecionado
      websocketClient.send({
        command: 'check_pair_availability',
        pair: selectedPair
      })
    }
  })

  // Event listener para o botão diagnose-pair
  const diagnoseBtn = document.getElementById('diagnose-pair')
  if (diagnoseBtn) {
    diagnoseBtn.addEventListener('click', function () {
      const selectedPair = document.getElementById('par').value
      if (selectedPair !== 'TODOS') {
        diagnosePair(selectedPair)
      } else {
        logar('⚠️ Selecione um par específico para diagnóstico')
      }
    })
  }
})

// Adicionar evento de visibilidade para reforçar a conexão quando a página voltar a ser visível
document.addEventListener('visibilitychange', function () {
  if (document.visibilityState === 'visible') {
    if (websocketClient && !websocketClient.isConnected) {
      logar('Página voltou a ser visível, verificando conexão...')
      connectWebSocket()
    }
  }
})

// Adicionar verificação periódica do estado da conexão
setInterval(function () {
  if (websocketClient && !websocketClient.isConnected && roboLigado) {
    logar('⚠️ Detectada desconexão enquanto robô está ativo. Reconectando...')
    connectWebSocket()
  }
}, 10000)
