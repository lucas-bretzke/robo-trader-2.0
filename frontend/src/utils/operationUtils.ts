export interface Operation {
  id: number
  timestamp: string
  action: string
  asset: string
  amount: number
  result: 'win' | 'loss' | 'pending'
  profit?: number
}

// Get operations from localStorage
export const getOperations = (): Operation[] => {
  try {
    const data = localStorage.getItem('operationHistory')
    return data ? JSON.parse(data) : []
  } catch (error) {
    console.error('Failed to parse operations from localStorage:', error)
    return []
  }
}

// Save operations to localStorage
export const saveOperations = (operations: Operation[]): void => {
  try {
    localStorage.setItem('operationHistory', JSON.stringify(operations))
  } catch (error) {
    console.error('Failed to save operations to localStorage:', error)
  }
}

// Add new operation
export const addOperation = (
  operation: Omit<Operation, 'id' | 'timestamp'>
): void => {
  const operations = getOperations()
  const newOperation: Operation = {
    ...operation,
    id: Date.now(),
    timestamp: new Date().toISOString()
  }

  operations.unshift(newOperation)
  saveOperations(operations)
}

// Update operation result
export const updateOperationResult = (
  id: number,
  result: 'win' | 'loss',
  profit?: number
): boolean => {
  const operations = getOperations()
  const index = operations.findIndex(op => op.id === id)

  if (index !== -1) {
    operations[index].result = result
    if (profit !== undefined) {
      operations[index].profit = profit
    }
    saveOperations(operations)
    return true
  }
  return false
}

// Clear all operations
export const clearOperations = (): void => {
  localStorage.removeItem('operationHistory')
}
