import { BINARY_OPTIONS } from '../config/binaries'

export async function fetchMarketData() {
  // Instead of fetching all available options
  // Only fetch data for the predefined list

  const results = []

  for (const option of BINARY_OPTIONS) {
    try {
      // Your existing code for fetching a single option
      const data = await fetchDataForOption(option)
      results.push(data)
    } catch (error) {
      console.error(`Error fetching data for ${option}:`, error)
    }
  }

  return results
}

async function fetchDataForOption(optionSymbol: string) {
  // Implementation for fetching data for a single option
  const response = await fetch(
    `https://api.example.com/market-data/${optionSymbol}`
  )
  if (!response.ok) {
    throw new Error(`Failed to fetch data for ${optionSymbol}`)
  }
  return response.json()
}
