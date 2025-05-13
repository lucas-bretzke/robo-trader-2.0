import React, { useEffect, useState } from 'react'
import styled from 'styled-components'
import { FaRobot, FaChartLine, FaHistory, FaCog } from 'react-icons/fa'
import { useRobot } from '../context/RobotContext'
import StatusCard from './StatusCard'
import RobotConfiguration from './RobotConfiguration'
import TradingChart from './TradingChart'
import OperationsHistory from './OperationsHistory'
import { fetchBalance } from '../services/api'

const MainContainer = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: ${props => props.theme.colors.background};
  padding: 20px;
`

const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`

const LogoContainer = styled.div`
  display: flex;
  align-items: center;
  color: ${props => props.theme.colors.primary};
`

const Logo = styled(FaRobot)`
  font-size: 2rem;
  margin-right: 12px;
`

const AppName = styled.h1`
  font-size: 1.8rem;
  font-weight: 600;
  color: ${props => props.theme.colors.textPrimary};
`

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
`

const MainContent = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;

  @media (min-width: 1024px) {
    grid-template-columns: 1fr 1fr;
  }
`

interface GridContainerProps {
  $gridArea?: string // Using transient prop with $ prefix
}

const GridContainer = styled.div<GridContainerProps>`
  background: ${props => props.theme.colors.cardBackground};
  border-radius: ${props => props.theme.borderRadius.md};
  padding: 20px;
  box-shadow: ${props => props.theme.shadows.sm};
  grid-area: ${props => props.$gridArea || 'auto'};
  overflow: hidden;
  display: flex;
  flex-direction: column;
`

const SectionTitle = styled.h2`
  font-size: 18px;
  margin-bottom: 20px;
  color: ${props => props.theme.colors.textPrimary};
  display: flex;
  align-items: center;
  gap: 10px;
`

const SectionContainer = styled.div`
  @media (min-width: ${({ theme }) => theme.md}) {
    // ...existing responsive styles...
  }
`

const SectionContent = styled.div`
  flex: 1;
  overflow: auto;
`

const MainScreen: React.FC = () => {
  const { status: robotStatus } = useRobot()
  const [balance, setBalance] = useState(0)

  useEffect(() => {
    // Fetch initial balance
    fetchBalance().then(data => {
      if (data !== null) setBalance(data)
    })

    // Periodically update balance
    const interval = setInterval(() => {
      fetchBalance().then(data => {
        if (data !== null) setBalance(data)
      })
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const winRate =
    robotStatus.operations_count > 0
      ? ((robotStatus.wins / robotStatus.operations_count) * 100).toFixed(2)
      : '0.00'

  return (
    <MainContainer>
      <Header>
        <LogoContainer>
          <Logo />
          <AppName>IQ Option Trader</AppName>
        </LogoContainer>
      </Header>

      <StatsContainer>
        <StatusCard
          title='Account Balance'
          value={`$${balance.toFixed(2)}`}
          label='Account Balance'
        />
        <StatusCard
          title='Trading Profit'
          value={`$${robotStatus.profit.toFixed(2)}`}
          label={`${robotStatus.wins} wins / ${robotStatus.losses} losses`}
          isPositive={robotStatus.profit >= 0}
        />
        <StatusCard
          title='Win Rate'
          value={`${winRate}%`}
          label={`Total trades: ${robotStatus.operations_count}`}
          isPositive={parseFloat(winRate) >= 50}
        />
        <StatusCard
          title='Robot Status'
          value={robotStatus.status === 'active' ? 'Running' : 'Stopped'}
          label={
            robotStatus.last_operation
              ? `Last op: ${new Date(
                  robotStatus.last_operation.timestamp
                ).toLocaleTimeString()}`
              : 'No operations yet'
          }
          isPositive={robotStatus.status === 'active'}
        />
      </StatsContainer>

      <MainContent>
        <GridContainer>
          <SectionTitle>
            <FaCog /> Robot Configuration
          </SectionTitle>
          <SectionContent>
            <RobotConfiguration />
          </SectionContent>
        </GridContainer>

        <GridContainer>
          <SectionTitle>
            <FaChartLine /> Trading Performance
          </SectionTitle>
          <SectionContent>
            <TradingChart />
          </SectionContent>
        </GridContainer>

        <GridContainer $gridArea='span 1 / span 2'>
          <SectionTitle>
            <FaHistory /> Operations History
          </SectionTitle>
          <SectionContent>
            <OperationsHistory />
          </SectionContent>
        </GridContainer>
      </MainContent>
    </MainContainer>
  )
}

export default MainScreen
