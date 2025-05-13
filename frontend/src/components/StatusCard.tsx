import React from 'react'
import styled from 'styled-components'

interface StatusCardProps {
  title: string
  value: string
  label?: string
  isPositive?: boolean
  icon?: React.ReactNode
}

// Using transient props (with $ prefix) to avoid DOM warnings
const StatusCardContainer = styled.div`
  background-color: ${({ theme }) => theme.colors.cardBackground};
  border-radius: ${({ theme }) => theme.borderRadius.md};
  box-shadow: ${({ theme }) => theme.shadows.small};
  padding: ${({ theme }) => theme.spacing.lg};
  margin-bottom: ${({ theme }) => theme.spacing.md};
`

const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
`

const Title = styled.h3`
  font-size: 0.9rem;
  color: ${props => props.theme.colors.textSecondary};
  font-weight: 500;
  margin: 0;
`

const IconContainer = styled.div`
  color: ${props => props.theme.colors.primary};
  display: flex;
  align-items: center;
  justify-content: center;
`

const Value = styled.div<{ isPositive?: boolean }>`
  font-size: 1.75rem;
  font-weight: 600;
  margin: 4px 0;
  color: ${props => {
    if (props.isPositive === undefined) return props.theme.colors.textPrimary
    return props.isPositive
      ? props.theme.colors.success
      : props.theme.colors.danger
  }};
`

const Label = styled.div`
  font-size: 0.85rem;
  color: ${props => props.theme.colors.textSecondary};
`

const StatusCard: React.FC<StatusCardProps> = ({
  title,
  value,
  label,
  isPositive,
  icon
}) => {
  return (
    <StatusCardContainer>
      <CardHeader>
        <Title>{title}</Title>
        {icon && <IconContainer>{icon}</IconContainer>}
      </CardHeader>
      <Value isPositive={isPositive}>{value}</Value>
      {label && <Label>{label}</Label>}
    </StatusCardContainer>
  )
}

export default StatusCard
