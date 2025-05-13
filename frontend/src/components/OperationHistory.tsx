import React, { useState, useEffect } from 'react'
import './OperationHistory.css'

interface Operation {
  id: number
  timestamp: string
  action: string
  asset: string
  amount: number
  result: 'win' | 'loss' | 'pending'
  profit?: number
}

// Utility functions for localStorage
const getOperationsFromStorage = (): Operation[] => {
  try {
    const storedOperations = localStorage.getItem('operationHistory')
    return storedOperations ? JSON.parse(storedOperations) : []
  } catch (error) {
    console.error('Error retrieving operations from localStorage:', error)
    return []
  }
}

const saveOperationsToStorage = (operations: Operation[]): void => {
  try {
    localStorage.setItem('operationHistory', JSON.stringify(operations))
  } catch (error) {
    console.error('Error saving operations to localStorage:', error)
  }
}

// Mock function to add sample operations (for testing)
export const addSampleOperation = (): void => {
  const operations = getOperationsFromStorage()
  const newOperation: Operation = {
    id: Date.now(),
    timestamp: new Date().toISOString(),
    action: Math.random() > 0.5 ? 'BUY' : 'SELL',
    asset: ['EUR/USD', 'BTC/USD', 'APPLE', 'AMAZON'][
      Math.floor(Math.random() * 4)
    ],
    amount: parseFloat((Math.random() * 100 + 10).toFixed(2)),
    result: ['win', 'loss', 'pending'][Math.floor(Math.random() * 3)] as
      | 'win'
      | 'loss'
      | 'pending'
  }

  if (newOperation.result !== 'pending') {
    newOperation.profit =
      newOperation.result === 'win'
        ? parseFloat((newOperation.amount * 0.8).toFixed(2))
        : parseFloat((-newOperation.amount).toFixed(2))
  }

  operations.unshift(newOperation) // Add to the beginning to show newest first
  saveOperationsToStorage(operations)
}

interface OperationHistoryProps {
  refreshInterval?: number // in milliseconds
}

const OperationHistory: React.FC<OperationHistoryProps> = ({
  refreshInterval = 10000
}) => {
  const [operations, setOperations] = useState<Operation[]>([])

  const loadOperations = () => {
    const loadedOperations = getOperationsFromStorage()
    setOperations(loadedOperations)
  }

  useEffect(() => {
    loadOperations()

    // Refresh data at specified interval
    const intervalId = setInterval(loadOperations, refreshInterval)

    return () => clearInterval(intervalId)
  }, [refreshInterval])

  const clearHistory = () => {
    if (
      window.confirm('Are you sure you want to clear all operation history?')
    ) {
      localStorage.removeItem('operationHistory')
      setOperations([])
    }
  }

  return (
    <div className='operation-history'>
      <div className='history-header'>
        <h2>Operation History</h2>
        <div className='history-actions'>
          <button onClick={loadOperations} className='refresh-btn'>
            Refresh
          </button>
          <button onClick={clearHistory} className='clear-btn'>
            Clear History
          </button>
        </div>
      </div>

      {operations.length === 0 ? (
        <p>No operations performed yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Action</th>
              <th>Asset</th>
              <th>Amount</th>
              <th>Result</th>
              <th>Profit/Loss</th>
            </tr>
          </thead>
          <tbody>
            {operations.map(op => (
              <tr key={op.id} className={op.result}>
                <td>{new Date(op.timestamp).toLocaleString()}</td>
                <td>{op.action}</td>
                <td>{op.asset}</td>
                <td>${op.amount.toFixed(2)}</td>
                <td>{op.result}</td>
                <td>
                  {op.profit !== undefined
                    ? (op.profit > 0 ? '+' : '') + op.profit.toFixed(2)
                    : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default OperationHistory
