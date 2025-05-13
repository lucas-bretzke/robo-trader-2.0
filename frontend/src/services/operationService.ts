interface Operation {
  id: number
  timestamp: string
  action: string
  asset: string
  amount: number
  result: 'win' | 'loss' | 'pending'
  profit?: number
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000'

export const fetchOperationHistory = async (): Promise<Operation[]> => {
  try {
    const response = await fetch(`${API_URL}/api/operations/history`)

    if (!response.ok) {
      throw new Error(`Error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Failed to fetch operation history:', error)
    throw error
  }
}

export const fetchLatestOperations = async (
  limit = 10
): Promise<Operation[]> => {
  try {
    const response = await fetch(
      `${API_URL}/api/operations/latest?limit=${limit}`
    )

    if (!response.ok) {
      throw new Error(`Error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Failed to fetch latest operations:', error)
    throw error
  }
}
