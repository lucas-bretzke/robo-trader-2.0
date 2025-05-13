import axios from 'axios'
import { API_URL } from '../config'
import { RobotStatus } from '../context/RobotContext'

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_URL
})

// Types
export interface LoginCredentials {
  email: string
  password: string
  accountType: string
}

export interface LoginResponse {
  success: boolean
  message: string
  balance: number
  account_type: string
}

export interface RobotConfig {
  candle_time: number
  operation_time: number
  selected_assets: string[]
  money_management: string
  entry_amount: number
  martingale_factor: number
  stop_loss: number
  stop_gain: number
  allowed_hours: {
    start: string
    end: string
  }
}

// API functions
export const login = async (credentials: LoginCredentials) => {
  try {
    const response = await api.post<LoginResponse>('/connect', credentials)
    return response.data
  } catch (error) {
    console.error('Login error:', error)
    throw error
  }
}

export const fetchBalance = async () => {
  try {
    const response = await api.get('/balance')
    return response.data.success ? response.data.balance : null
  } catch (error) {
    console.error('Balance fetch error:', error)
    return null
  }
}

export const fetchAssets = async (type = 'digital') => {
  try {
    const response = await api.get(`/assets?type=${type}`)
    return response.data.success ? response.data.assets : []
  } catch (error) {
    console.error('Assets fetch error:', error)
    return []
  }
}

export const startRobot = async (config: RobotConfig) => {
  try {
    const response = await api.post('/start', config)
    return response.data
  } catch (error) {
    console.error('Start robot error:', error)
    throw error
  }
}

export const stopRobot = async () => {
  try {
    const response = await api.post('/stop')
    return response.data
  } catch (error) {
    console.error('Stop robot error:', error)
    throw error
  }
}

export const fetchRobotStatus = async () => {
  try {
    const response = await api.get('/status')
    return response.data.success ? (response.data.status as RobotStatus) : null
  } catch (error) {
    console.error('Status fetch error:', error)
    return null
  }
}

export const fetchHistory = async (date?: string) => {
  try {
    const url = date ? `/history?date=${date}` : '/history'
    const response = await api.get(url)
    return response.data.success ? response.data.history : []
  } catch (error) {
    console.error('History fetch error:', error)
    return []
  }
}

export const clearHistory = async () => {
  try {
    const response = await api.post('/history/clear')
    return response.data
  } catch (error) {
    console.error('Clear history error:', error)
    throw error
  }
}

export const testEntry = async () => {
  try {
    const response = await api.post('/test-entry')
    return response.data
  } catch (error) {
    console.error('Test entry error:', error)
    throw error
  }
}

export const checkApiHealth = async () => {
  try {
    const response = await api.get('/health')
    return response.data.success
  } catch (error) {
    console.error('API health check error:', error)
    return false
  }
}
