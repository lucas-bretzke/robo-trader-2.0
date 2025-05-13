import React from 'react'
import styled from 'styled-components'
import { FaRobot } from 'react-icons/fa'
import LoginForm from './LoginForm'

const LoginScreenContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: ${props => props.theme.colors.background};
  flex-direction: column;
`

const LogoContainer = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  color: ${props => props.theme.colors.primary};
`

const Logo = styled(FaRobot)`
  font-size: 2.5rem;
  margin-right: 12px;
`

const AppName = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  color: ${props => props.theme.colors.textPrimary};
`

const AppDescription = styled.p`
  margin: 8px 0 32px;
  color: ${props => props.theme.colors.textSecondary};
  text-align: center;
  max-width: 500px;
`

const LoginScreen: React.FC = () => {
  return (
    <LoginScreenContainer>
      <LogoContainer>
        <Logo />
        <AppName>IQ Option Trader</AppName>
      </LogoContainer>

      <AppDescription>
        Connect to your IQ Option account and start automated trading with our
        advanced trading robot.
      </AppDescription>

      <LoginForm />
    </LoginScreenContainer>
  )
}

export default LoginScreen
