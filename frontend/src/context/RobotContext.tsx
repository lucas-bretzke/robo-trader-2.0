import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode
} from 'react'

// Types
type Operation = {
  id: string
  type: 'CALL' | 'PUT'
  amount: number
  result: 'WIN' | 'LOSS' | 'DRAW'
  profit: number
  timestamp: string
}

type RobotStatus = {
  status: 'active' | 'inactive' | 'error'
  profit: number
  wins: number
  losses: number
  operations_count: number
  last_operation: Operation | null
}

type RobotParameters = {
  timeframe: string
  asset: string
  amount: string
  strategy: string
}

interface RobotContextType {
  isRunning: boolean
  status: RobotStatus
  startRobot: (params: RobotParameters) => void
  stopRobot: () => void
}

// Default values
const defaultStatus: RobotStatus = {
  status: 'inactive',
  profit: 0,
  wins: 0,
  losses: 0,
  operations_count: 0,
  last_operation: null
}

// Create context
const RobotContext = createContext<RobotContextType>({
  isRunning: false,
  status: defaultStatus,
  startRobot: () => {},
  stopRobot: () => {}
})

// Provider component
export const RobotProvider: React.FC<{ children: ReactNode }> = ({
  children
}) => {
  const [isRunning, setIsRunning] = useState(false)
  const [status, setStatus] = useState<RobotStatus>(defaultStatus)

  // Mock API functions
  const startRobot = (params: RobotParameters) => {
    console.log('Starting robot with params:', params)
    setIsRunning(true)
    setStatus(prev => ({
      ...prev,
      status: 'active'
    }))
    // In a real app, you would make an API call here
  }

  const stopRobot = () => {
    setIsRunning(false)
    setStatus(prev => ({
      ...prev,
      status: 'inactive'
    }))
    // In a real app, you would make an API call here
  }

  // Simulate operations coming in when the robot is running
  useEffect(() => {
    let interval: number | null = null

    if (isRunning) {
      interval = window.setInterval(() => {
        // Simulate a new operation randomly
        const isWin = Math.random() > 0.4
        const profit = isWin ? 8.5 : -10

        const newOperation: Operation = {
          id: Date.now().toString(),
          type: Math.random() > 0.5 ? 'CALL' : 'PUT',
          amount: 10,
          result: isWin ? 'WIN' : 'LOSS',
          profit: profit,
          timestamp: new Date().toISOString()
        }

        setStatus(prev => ({
          ...prev,
          profit: prev.profit + profit,
          wins: isWin ? prev.wins + 1 : prev.wins,
          losses: !isWin ? prev.losses + 1 : prev.losses,
          operations_count: prev.operations_count + 1,
          last_operation: newOperation
        }))
      }, 10000) // Simulate a new operation every 10 seconds
    }

    return () => {
      if (interval) {
        clearInterval(interval)
      }
    }
  }, [isRunning])

  return (
    <RobotContext.Provider
      value={{
        isRunning,
        status,
        startRobot,
        stopRobot
      }}
    >
      {children}
    </RobotContext.Provider>
  )
}

// Hook for using the robot context
export const useRobot = () => useContext(RobotContext)
