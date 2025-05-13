import React, { useState } from 'react'
import styled from 'styled-components'
import { useRobot } from '../context/RobotContext'
import Button from './common/Button'

const ControlsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`

const ControlsRow = styled.div`
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
`

const ParametersGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 15px;
  margin-top: 15px;
`

const ParameterInput = styled.div`
  display: flex;
  flex-direction: column;
  gap: 5px;

  label {
    font-size: 14px;
    font-weight: 500;
  }

  input,
  select {
    padding: 8px;
    border: 1px solid #ced4da;
    border-radius: ${props => props.theme.radius.sm};
    font-size: 14px;
  }
`

const RobotControls: React.FC = () => {
  const { isRunning, startRobot, stopRobot } = useRobot()
  const [parameters, setParameters] = useState({
    timeframe: '5',
    asset: 'EURUSD',
    amount: '10',
    strategy: 'default'
  })

  const handleParameterChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    setParameters(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleStartRobot = () => {
    startRobot(parameters)
  }

  return (
    <ControlsContainer>
      <ControlsRow>
        <Button
          variant={isRunning ? 'danger' : 'success'}
          onClick={isRunning ? stopRobot : handleStartRobot}
        >
          {isRunning ? 'Stop Robot' : 'Start Robot'}
        </Button>
      </ControlsRow>

      <ParametersGrid>
        <ParameterInput>
          <label htmlFor='timeframe'>Timeframe</label>
          <select
            id='timeframe'
            name='timeframe'
            value={parameters.timeframe}
            onChange={handleParameterChange}
            disabled={isRunning}
          >
            <option value='1'>1 minute</option>
            <option value='5'>5 minutes</option>
            <option value='15'>15 minutes</option>
            <option value='30'>30 minutes</option>
            <option value='60'>1 hour</option>
          </select>
        </ParameterInput>

        <ParameterInput>
          <label htmlFor='asset'>Asset</label>
          <select
            id='asset'
            name='asset'
            value={parameters.asset}
            onChange={handleParameterChange}
            disabled={isRunning}
          >
            <option value='EURUSD'>EUR/USD</option>
            <option value='GBPUSD'>GBP/USD</option>
            <option value='USDJPY'>USD/JPY</option>
            <option value='BTCUSD'>BTC/USD</option>
          </select>
        </ParameterInput>

        <ParameterInput>
          <label htmlFor='amount'>Amount ($)</label>
          <input
            id='amount'
            name='amount'
            type='number'
            value={parameters.amount}
            onChange={handleParameterChange}
            disabled={isRunning}
            min='1'
          />
        </ParameterInput>

        <ParameterInput>
          <label htmlFor='strategy'>Strategy</label>
          <select
            id='strategy'
            name='strategy'
            value={parameters.strategy}
            onChange={handleParameterChange}
            disabled={isRunning}
          >
            <option value='default'>Default</option>
            <option value='macd'>MACD</option>
            <option value='rsi'>RSI</option>
            <option value='bollinger'>Bollinger Bands</option>
          </select>
        </ParameterInput>
      </ParametersGrid>
    </ControlsContainer>
  )
}

export default RobotControls
