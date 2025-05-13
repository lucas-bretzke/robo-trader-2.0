import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { format } from 'date-fns'
import { FaArrowUp, FaArrowDown, FaBroom, FaCalendarAlt } from 'react-icons/fa'
import { fetchHistory, clearHistory } from '../services/api'
import Button from './common/Button'

interface Operation {
  asset: string
  direction: string
  amount: number
  result: number
  outcome: string
  timestamp: string
}

const HistoryContainer = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
`

const HistoryControls = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  align-items: center;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
`

const DateFilter = styled.div`
  display: flex;
  gap: 10px;
  align-items: center;
`

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
`

const TableHeader = styled.th`
  text-align: left;
  padding: 12px;
  background-color: ${props => props.theme.colors.sectionBackground};
  color: ${props => props.theme.colors.textPrimary};
  font-weight: 600;
  border-bottom: 1px solid ${props => props.theme.colors.border};

  @media (max-width: 768px) {
    padding: 8px;
  }
`

const TableRow = styled.tr`
  &:nth-child(even) {
    background-color: ${props => props.theme.colors.sectionBackground};
  }

  &:hover {
    background-color: ${props => props.theme.colors.primaryLight};
  }
`

const TableCell = styled.td`
  padding: 12px;
  border-bottom: 1px solid ${props => props.theme.colors.border};

  @media (max-width: 768px) {
    padding: 8px;
  }
`

const Outcome = styled.span<{ type: string }>`
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: 500;
  font-size: 0.85rem;
  background-color: ${props => {
    switch (props.type) {
      case 'win':
        return props.theme.colors.successLight
      case 'loss':
        return props.theme.colors.dangerLight
      default:
        return props.theme.colors.warningLight
    }
  }};
  color: ${props => {
    switch (props.type) {
      case 'win':
        return props.theme.colors.success
      case 'loss':
        return props.theme.colors.danger
      default:
        return props.theme.colors.warning
    }
  }};
`

const Direction = styled.div<{ type: string }>`
  display: flex;
  align-items: center;
  gap: 5px;
  color: ${props =>
    props.type === 'call'
      ? props.theme.colors.success
      : props.theme.colors.danger};
`

const NoDataMessage = styled.div`
  text-align: center;
  padding: 30px;
  color: ${props => props.theme.colors.textSecondary};
`

const EmptyTable = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px 0;
  color: ${props => props.theme.colors.textSecondary};
  border: 1px dashed ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.md};
`

const OperationsHistory: React.FC = () => {
  const [operations, setOperations] = useState<Operation[]>([])
  const [loading, setLoading] = useState(false)
  const [dateFilter, setDateFilter] = useState<string | undefined>()

  useEffect(() => {
    loadOperations()

    // Refresh operations every minute
    const interval = setInterval(() => {
      loadOperations()
    }, 60000)

    return () => clearInterval(interval)
  }, [dateFilter])

  const loadOperations = async () => {
    setLoading(true)
    try {
      const history = await fetchHistory(dateFilter)
      setOperations(history)
    } catch (error) {
      console.error('Failed to load operations history:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleClearHistory = async () => {
    if (!window.confirm('Are you sure you want to clear all history?')) {
      return
    }

    setLoading(true)
    try {
      await clearHistory()
      setOperations([])
    } catch (error) {
      console.error('Failed to clear history:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDateFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDateFilter(e.target.value || undefined)
  }

  return (
    <HistoryContainer>
      <HistoryControls>
        <DateFilter>
          <FaCalendarAlt />
          <input
            type='date'
            value={dateFilter || ''}
            onChange={handleDateFilterChange}
          />
        </DateFilter>

        <Button
          variant='danger'
          size='sm'
          onClick={handleClearHistory}
          disabled={loading || operations.length === 0}
        >
          <FaBroom /> Clear History
        </Button>
      </HistoryControls>

      {loading ? (
        <NoDataMessage>Loading operations...</NoDataMessage>
      ) : operations.length > 0 ? (
        <Table>
          <thead>
            <tr>
              <TableHeader>Time</TableHeader>
              <TableHeader>Asset</TableHeader>
              <TableHeader>Direction</TableHeader>
              <TableHeader>Amount</TableHeader>
              <TableHeader>Result</TableHeader>
              <TableHeader>Outcome</TableHeader>
            </tr>
          </thead>
          <tbody>
            {operations.map((op, index) => (
              <TableRow key={index}>
                <TableCell>
                  {format(new Date(op.timestamp), 'HH:mm:ss')}
                </TableCell>
                <TableCell>{op.asset}</TableCell>
                <TableCell>
                  <Direction type={op.direction.toLowerCase()}>
                    {op.direction.toLowerCase() === 'call' ? (
                      <>
                        <FaArrowUp /> Call
                      </>
                    ) : (
                      <>
                        <FaArrowDown /> Put
                      </>
                    )}
                  </Direction>
                </TableCell>
                <TableCell>${op.amount.toFixed(2)}</TableCell>
                <TableCell>${op.result.toFixed(2)}</TableCell>
                <TableCell>
                  <Outcome type={op.outcome.toLowerCase()}>
                    {op.outcome}
                  </Outcome>
                </TableCell>
              </TableRow>
            ))}
          </tbody>
        </Table>
      ) : (
        <EmptyTable>
          <p>No operations history found</p>
        </EmptyTable>
      )}
    </HistoryContainer>
  )
}

export default OperationsHistory
