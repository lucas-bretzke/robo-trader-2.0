import React from 'react'
import styled from 'styled-components'
import { FaPowerOff, FaHistory, FaChartLine, FaCog } from 'react-icons/fa'
import { useUser } from '../context/UserContext'
import { useNotebook } from '../context/NotebookContext'
import { useRobot } from '../context/RobotContext'
import StatusCard from './StatusCard'
import RobotControls from './RobotControls'
import TradingChart from './TradingChart'
import OperationsHistory from './OperationsHistory'
import Button from './common/Button'

const DashboardContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  padding-left: 30px;
`

const HeaderRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
`

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
`

const Section = styled.section`
  background: ${props => props.theme.colors.cardBackground};
  border-radius: ${props => props.theme.radius.md};
  padding: 20px;
  box-shadow: ${props => props.theme.shadows.sm};
  margin-bottom: 20px;
`

const SectionTitle = styled.h2`
  font-size: 18px;
  margin-bottom: 20px;
  color: ${props => props.theme.colors.textPrimary};
  display: flex;
  align-items: center;
  gap: 10px;
`

const TabContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`

const Dashboard: React.FC = () => {
  const { user, logout } = useUser()
  const { activeTab } = useNotebook()
  const { status: robotStatus } = useRobot()

  const winRate =
    robotStatus.operations_count > 0
      ? ((robotStatus.wins / robotStatus.operations_count) * 100).toFixed(2)
      : '0.00'

  return (
    <DashboardContainer>
      <HeaderRow>
        <h1>IQ Option Trader Dashboard</h1>
        <Button variant='danger' onClick={logout}>
          <FaPowerOff /> Logout
        </Button>
      </HeaderRow>

      <StatsContainer>
        <StatusCard
          title='Account Balance'
          value={`$${user.balance.toFixed(2)}`}
          label={`Account Type: ${user.accountType}`}
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

      {activeTab === 'controls' && (
        <TabContent>
          <Section>
            <SectionTitle>
              <FaCog /> Robot Controls
            </SectionTitle>
            <RobotControls />
          </Section>
        </TabContent>
      )}

      {activeTab === 'chart' && (
        <TabContent>
          <Section>
            <SectionTitle>
              <FaChartLine /> Trading Performance
            </SectionTitle>
            <TradingChart />
          </Section>
        </TabContent>
      )}

      {activeTab === 'history' && (
        <TabContent>
          <Section>
            <SectionTitle>
              <FaHistory /> Operations History
            </SectionTitle>
            <OperationsHistory />
          </Section>
        </TabContent>
      )}
    </DashboardContainer>
  )
}

export default Dashboard
