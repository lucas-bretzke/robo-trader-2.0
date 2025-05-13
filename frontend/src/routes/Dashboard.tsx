import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './Dashboard.css'

const Dashboard: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false)
  const [balance, setBalance] = useState(1000)
  const [settings, setSettings] = useState({
    tradeAmount: 10,
    stopLoss: 100,
    takeProfit: 200,
    strategy: 'MHI',
    martingaleLevel: 2
  })
  const navigate = useNavigate()

  // Check if user is logged in
  useEffect(() => {
    const credentials = localStorage.getItem('iqOptionCredentials')
    if (!credentials) {
      navigate('/')
    }
  }, [navigate])

  const handleStartStop = () => {
    setIsRunning(!isRunning)
  }

  const handleSettingsChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    setSettings(prev => ({
      ...prev,
      [name]: name === 'strategy' ? value : Number(value)
    }))
  }

  const handleLogout = () => {
    localStorage.removeItem('iqOptionCredentials')
    navigate('/')
  }

  // Get email from localStorage for display
  const getUserEmail = (): string => {
    try {
      const credentials = localStorage.getItem('iqOptionCredentials')
      if (credentials) {
        const { email } = JSON.parse(credentials)
        return email
      }
    } catch (e) {
      console.error('Error parsing credentials:', e)
    }
    return ''
  }

  return (
    <div className='dashboard'>
      <header className='dashboard-header'>
        <h1>IQ Option Robot Trader</h1>
        <div className='user-controls'>
          <span className='user-email'>{getUserEmail()}</span>
          <button className='logout-button' onClick={handleLogout}>
            Sair
          </button>
        </div>
      </header>

      <div className='status-bar'>
        <div className='status-indicator'>
          Status:{' '}
          <span className={isRunning ? 'status-active' : 'status-inactive'}>
            {isRunning ? 'Ativo' : 'Inativo'}
          </span>
        </div>
      </div>

      <div className='dashboard-content'>
        <div className='balance-section'>
          <h2>Saldo da Conta</h2>
          <div className='balance-amount'>R$ {balance.toFixed(2)}</div>
        </div>

        <div className='trading-section'>
          <h2>Estatísticas de Negociação</h2>
          <div className='stats-grid'>
            <div className='stat-item'>
              <span className='stat-label'>Negociações</span>
              <span className='stat-value'>24</span>
            </div>
            <div className='stat-item'>
              <span className='stat-label'>Vencedoras</span>
              <span className='stat-value success'>18</span>
            </div>
            <div className='stat-item'>
              <span className='stat-label'>Perdedoras</span>
              <span className='stat-value danger'>6</span>
            </div>
            <div className='stat-item'>
              <span className='stat-label'>Taxa de Acerto</span>
              <span className='stat-value'>75%</span>
            </div>
          </div>
        </div>

        <div className='settings-section'>
          <h2>Configurações do Robô</h2>
          <div className='settings-form'>
            <div className='form-group'>
              <label htmlFor='tradeAmount'>Valor da Entrada (R$)</label>
              <input
                type='number'
                id='tradeAmount'
                name='tradeAmount'
                value={settings.tradeAmount}
                onChange={handleSettingsChange}
              />
            </div>
            <div className='form-group'>
              <label htmlFor='strategy'>Estratégia</label>
              <select
                id='strategy'
                name='strategy'
                value={settings.strategy}
                onChange={handleSettingsChange}
              >
                <option value='MHI'>MHI</option>
                <option value='MHI Maioria'>MHI Maioria</option>
                <option value='MHI3'>MHI3</option>
                <option value='MILHÃO'>MILHÃO</option>
              </select>
            </div>
            <div className='form-group'>
              <label htmlFor='martingaleLevel'>Nível de Martingale</label>
              <input
                type='number'
                id='martingaleLevel'
                name='martingaleLevel'
                value={settings.martingaleLevel}
                onChange={handleSettingsChange}
                min='0'
                max='5'
              />
            </div>
            <div className='form-group'>
              <label htmlFor='stopLoss'>Stop Loss (R$)</label>
              <input
                type='number'
                id='stopLoss'
                name='stopLoss'
                value={settings.stopLoss}
                onChange={handleSettingsChange}
              />
            </div>
            <div className='form-group'>
              <label htmlFor='takeProfit'>Take Profit (R$)</label>
              <input
                type='number'
                id='takeProfit'
                name='takeProfit'
                value={settings.takeProfit}
                onChange={handleSettingsChange}
              />
            </div>
          </div>
        </div>
      </div>

      <div className='action-section'>
        <button
          className={`action-button ${isRunning ? 'stop' : 'start'}`}
          onClick={handleStartStop}
        >
          {isRunning ? 'Parar Robô' : 'Iniciar Robô'}
        </button>
      </div>

      <div className='trade-history'>
        <h2>Histórico de Operações</h2>
        <table className='history-table'>
          <thead>
            <tr>
              <th>Hora</th>
              <th>Ativo</th>
              <th>Entrada</th>
              <th>Direção</th>
              <th>Resultado</th>
            </tr>
          </thead>
          <tbody>
            <tr className='success-row'>
              <td>15:32:45</td>
              <td>EUR/USD</td>
              <td>R$ 10,00</td>
              <td>CALL</td>
              <td>+R$ 9,00</td>
            </tr>
            <tr className='danger-row'>
              <td>15:30:00</td>
              <td>EUR/USD</td>
              <td>R$ 10,00</td>
              <td>PUT</td>
              <td>-R$ 10,00</td>
            </tr>
            <tr className='success-row'>
              <td>15:25:00</td>
              <td>EUR/USD</td>
              <td>R$ 10,00</td>
              <td>CALL</td>
              <td>+R$ 9,00</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Dashboard
