import React, { useState, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import styled from 'styled-components'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { fetchHistory } from '../services/api'
import { format } from 'date-fns'

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

interface Operation {
  asset: string
  direction: string
  amount: number
  result: number
  outcome: string
  timestamp: string
}

const ChartContainer = styled.div`
  width: 100%;
  height: 300px;
  margin-bottom: 20px;
`

const ChartControls = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
  gap: 10px;
`

const FilterButton = styled.button<{ active: boolean }>`
  padding: 6px 12px;
  border-radius: ${props => props.theme.borderRadius.sm};
  background: ${props =>
    props.active
      ? props.theme.colors.primary
      : props.theme.colors.inputBackground};
  color: ${props =>
    props.active ? 'white' : props.theme.colors.textSecondary};
  border: 1px solid
    ${props =>
      props.active ? props.theme.colors.primary : props.theme.colors.border};
  cursor: pointer;
  font-size: 0.85rem;

  &:hover {
    background: ${props =>
      props.active
        ? props.theme.colors.primaryHover
        : props.theme.colors.primaryLight};
  }
`

const NoDataMessage = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
  width: 100%;
  color: ${props => props.theme.colors.textSecondary};
  font-size: 1.1rem;
`

const TradingChart: React.FC = () => {
  const [operations, setOperations] = useState<Operation[]>([])
  const [timeFilter, setTimeFilter] = useState<'day' | 'week' | 'month'>('day')

  useEffect(() => {
    loadOperations()

    // Refresh every minute
    const interval = setInterval(() => {
      loadOperations()
    }, 60000)

    return () => clearInterval(interval)
  }, [timeFilter])

  const loadOperations = async () => {
    // Get date filter based on selected timeframe
    let dateFilter: string | undefined
    const today = new Date()

    if (timeFilter === 'day') {
      dateFilter = format(today, 'yyyy-MM-dd')
    }

    try {
      const history = await fetchHistory(dateFilter)
      setOperations(history)
    } catch (error) {
      console.error('Failed to load operations history:', error)
    }
  }

  // Process data for chart
  const processChartData = () => {
    if (!operations.length) {
      return { labels: [], datasets: [] }
    }

    // Sort operations by timestamp
    const sortedOps = [...operations].sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )

    const labels: string[] = []
    const profitData: number[] = []
    let cumulativeProfit = 0

    sortedOps.forEach(op => {
      const time = format(new Date(op.timestamp), 'HH:mm')
      labels.push(time)
      cumulativeProfit += op.result
      profitData.push(cumulativeProfit)
    })

    return {
      labels,
      datasets: [
        {
          label: 'Cumulative Profit',
          data: profitData,
          borderColor: cumulativeProfit >= 0 ? '#22c55e' : '#ef4444',
          backgroundColor: 'rgba(0, 0, 0, 0)',
          tension: 0.1
        }
      ]
    }
  }

  const chartData = processChartData()

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `Profit: $${context.raw.toFixed(2)}`
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value: number) => `$${value.toFixed(2)}`
        }
      }
    }
  }

  return (
    <>
      <ChartControls>
        <FilterButton
          active={timeFilter === 'day'}
          onClick={() => setTimeFilter('day')}
        >
          Today
        </FilterButton>
        <FilterButton
          active={timeFilter === 'week'}
          onClick={() => setTimeFilter('week')}
        >
          This Week
        </FilterButton>
        <FilterButton
          active={timeFilter === 'month'}
          onClick={() => setTimeFilter('month')}
        >
          This Month
        </FilterButton>
      </ChartControls>

      <ChartContainer>
        {operations.length > 0 ? (
          <Line data={chartData} options={chartOptions} />
        ) : (
          <NoDataMessage>No trading data available</NoDataMessage>
        )}
      </ChartContainer>
    </>
  )
}

export default TradingChart
