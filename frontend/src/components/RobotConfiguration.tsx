import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import {
  FaPlay,
  FaStop,
  FaExchangeAlt,
  FaLock,
  FaEnvelope
} from 'react-icons/fa'
import { fetchAssets, startRobot, stopRobot, login } from '../services/api'
import { useRobot } from '../context/RobotContext'
import Button from './common/Button'
import Input from './common/Input'
import FormGroup, { Label, ErrorMessage } from './common/FormGroup'
import Select from './common/Select'

const ConfigContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`

const ConfigForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 15px;
`

const FieldSet = styled.fieldset`
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
  padding: 15px;
`

const Legend = styled.legend`
  padding: 0 10px;
  color: ${props => props.theme.colors.primary};
  font-weight: 600;
`

const Row = styled.div`
  display: flex;
  gap: 15px;
  margin-bottom: 10px;

  @media (max-width: 768px) {
    flex-direction: column;
  }
`

const Column = styled.div`
  flex: 1;
`

const AssetList = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
  max-height: 120px;
  overflow-y: auto;
`

const AssetChip = styled.div<{ selected: boolean }>`
  padding: 5px 10px;
  border-radius: 15px;
  background: ${props =>
    props.selected
      ? props.theme.colors.primaryLight
      : props.theme.colors.inputBackground};
  color: ${props =>
    props.selected
      ? props.theme.colors.primary
      : props.theme.colors.textSecondary};
  cursor: pointer;
  border: 1px solid
    ${props =>
      props.selected ? props.theme.colors.primary : props.theme.colors.border};
  font-size: 0.85rem;

  &:hover {
    background: ${props =>
      !props.selected && props.theme.colors.primaryLight + '50'};
  }
`

const ButtonGroup = styled.div`
  display: flex;
  gap: 10px;
  margin-top: 15px;
  justify-content: center;
`

const RobotConfiguration: React.FC = () => {
  const { isRunning, setIsRunning, updateStatus } = useRobot()
  const [availableAssets, setAvailableAssets] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [config, setConfig] = useState({
    email: '',
    password: '',
    accountType: 'PRACTICE',
    candle_time: 60,
    operation_time: 1,
    selected_assets: [] as string[],
    money_management: 'fixed',
    entry_amount: 2,
    martingale_factor: 2.0,
    stop_loss: 50,
    stop_gain: 100,
    allowed_hours: {
      start: '09:00',
      end: '18:00'
    }
  })

  useEffect(() => {
    loadAssets()
  }, [])

  const loadAssets = async () => {
    try {
      const assets = await fetchAssets('digital')
      setAvailableAssets(assets)
    } catch (error) {
      console.error('Failed to load assets:', error)
    }
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target

    if (name.includes('.')) {
      const [parent, child] = name.split('.')
      setConfig(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent as keyof typeof prev],
          [child]: value
        }
      }))
    } else {
      setConfig(prev => ({ ...prev, [name]: value }))
    }
  }

  const toggleAsset = (asset: string) => {
    setConfig(prev => {
      const selected = [...prev.selected_assets]
      if (selected.includes(asset)) {
        return { ...prev, selected_assets: selected.filter(a => a !== asset) }
      } else {
        return { ...prev, selected_assets: [...selected, asset] }
      }
    })
  }

  const connectToIQOption = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await login({
        email: config.email,
        password: config.password,
        accountType: config.accountType
      })

      if (response.success) {
        // After successful login, load assets again
        await loadAssets()
        setError(null)
      } else {
        setError(response.message || 'Failed to connect')
      }
    } catch (error) {
      setError('Connection failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  const handleStartRobot = async () => {
    if (config.selected_assets.length === 0) {
      setError('Please select at least one asset')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await startRobot(config)

      if (response.success) {
        setIsRunning(true)
        updateStatus({ status: 'active' })
      } else {
        setError(response.message || 'Failed to start robot')
      }
    } catch (error) {
      setError('Failed to start robot')
    } finally {
      setLoading(false)
    }
  }

  const handleStopRobot = async () => {
    setLoading(true)

    try {
      const response = await stopRobot()

      if (response.success) {
        setIsRunning(false)
        updateStatus({ status: 'inactive' })
      } else {
        setError(response.message || 'Failed to stop robot')
      }
    } catch (error) {
      setError('Failed to stop robot')
    } finally {
      setLoading(false)
    }
  }

  return (
    <ConfigContainer>
      {/* IQ Option Connection */}
      <FieldSet>
        <Legend>IQ Option Account</Legend>
        <ConfigForm onSubmit={connectToIQOption}>
          <Row>
            <Column>
              <FormGroup>
                <Label>Email</Label>
                <Input
                  type='email'
                  name='email'
                  value={config.email}
                  onChange={handleChange}
                  placeholder='IQ Option Email'
                  fullWidth
                  required
                  disabled={loading}
                />
              </FormGroup>
            </Column>

            <Column>
              <FormGroup>
                <Label>Password</Label>
                <Input
                  type='password'
                  name='password'
                  value={config.password}
                  onChange={handleChange}
                  placeholder='IQ Option Password'
                  fullWidth
                  required
                  disabled={loading}
                />
              </FormGroup>
            </Column>
          </Row>

          <Row>
            <Column>
              <FormGroup>
                <Label>Account Type</Label>
                <Select
                  name='accountType'
                  value={config.accountType}
                  onChange={handleChange}
                  fullWidth
                  disabled={loading}
                >
                  <option value='PRACTICE'>Demo Account</option>
                  <option value='REAL'>Real Account</option>
                </Select>
              </FormGroup>
            </Column>

            <Column>
              <Button
                type='submit'
                fullWidth
                disabled={loading || !config.email || !config.password}
              >
                Connect to IQ Option
              </Button>
            </Column>
          </Row>
        </ConfigForm>
      </FieldSet>

      {/* Trading Configuration */}
      <FieldSet>
        <Legend>Trading Configuration</Legend>
        <Row>
          <Column>
            <FormGroup>
              <Label>Candle Time (seconds)</Label>
              <Select
                name='candle_time'
                value={config.candle_time}
                onChange={handleChange}
                fullWidth
                disabled={loading || isRunning}
              >
                <option value={60}>1 minute</option>
                <option value={300}>5 minutes</option>
                <option value={900}>15 minutes</option>
              </Select>
            </FormGroup>
          </Column>

          <Column>
            <FormGroup>
              <Label>Operation Time (minutes)</Label>
              <Select
                name='operation_time'
                value={config.operation_time}
                onChange={handleChange}
                fullWidth
                disabled={loading || isRunning}
              >
                <option value={1}>1</option>
                <option value={2}>2</option>
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={15}>15</option>
              </Select>
            </FormGroup>
          </Column>
        </Row>

        <FormGroup>
          <Label>Select Assets to Trade</Label>
          <AssetList>
            {availableAssets.map(asset => (
              <AssetChip
                key={asset}
                selected={config.selected_assets.includes(asset)}
                onClick={() => toggleAsset(asset)}
              >
                {asset}
              </AssetChip>
            ))}
          </AssetList>
        </FormGroup>
      </FieldSet>

      {/* Money Management */}
      <FieldSet>
        <Legend>Money Management</Legend>
        <Row>
          <Column>
            <FormGroup>
              <Label>Strategy</Label>
              <Select
                name='money_management'
                value={config.money_management}
                onChange={handleChange}
                fullWidth
                disabled={loading || isRunning}
              >
                <option value='fixed'>Fixed</option>
                <option value='martingale'>Martingale</option>
              </Select>
            </FormGroup>
          </Column>

          <Column>
            <FormGroup>
              <Label>Entry Amount ($)</Label>
              <Input
                type='number'
                name='entry_amount'
                value={config.entry_amount}
                onChange={handleChange}
                min={1}
                fullWidth
                disabled={loading || isRunning}
              />
            </FormGroup>
          </Column>
        </Row>

        <Row>
          {config.money_management === 'martingale' && (
            <Column>
              <FormGroup>
                <Label>Martingale Factor</Label>
                <Input
                  type='number'
                  name='martingale_factor'
                  value={config.martingale_factor}
                  onChange={handleChange}
                  min={1.1}
                  step={0.1}
                  fullWidth
                  disabled={loading || isRunning}
                />
              </FormGroup>
            </Column>
          )}

          <Column>
            <FormGroup>
              <Label>Stop Loss ($)</Label>
              <Input
                type='number'
                name='stop_loss'
                value={config.stop_loss}
                onChange={handleChange}
                min={0}
                fullWidth
                disabled={loading || isRunning}
              />
            </FormGroup>
          </Column>

          <Column>
            <FormGroup>
              <Label>Stop Gain ($)</Label>
              <Input
                type='number'
                name='stop_gain'
                value={config.stop_gain}
                onChange={handleChange}
                min={0}
                fullWidth
                disabled={loading || isRunning}
              />
            </FormGroup>
          </Column>
        </Row>

        <Row>
          <Column>
            <FormGroup>
              <Label>Trading Hours Start</Label>
              <Input
                type='time'
                name='allowed_hours.start'
                value={config.allowed_hours.start}
                onChange={handleChange}
                fullWidth
                disabled={loading || isRunning}
              />
            </FormGroup>
          </Column>

          <Column>
            <FormGroup>
              <Label>Trading Hours End</Label>
              <Input
                type='time'
                name='allowed_hours.end'
                value={config.allowed_hours.end}
                onChange={handleChange}
                fullWidth
                disabled={loading || isRunning}
              />
            </FormGroup>
          </Column>
        </Row>
      </FieldSet>

      {error && <ErrorMessage>{error}</ErrorMessage>}

      <ButtonGroup>
        <Button
          variant='success'
          size='lg'
          onClick={handleStartRobot}
          disabled={loading || isRunning || config.selected_assets.length === 0}
        >
          <FaPlay /> Start Robot
        </Button>

        <Button
          variant='danger'
          size='lg'
          onClick={handleStopRobot}
          disabled={loading || !isRunning}
        >
          <FaStop /> Stop Robot
        </Button>
      </ButtonGroup>
    </ConfigContainer>
  )
}

export default RobotConfiguration
