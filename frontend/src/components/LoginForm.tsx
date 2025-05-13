import React, { useState } from 'react'
import styled from 'styled-components'
import { FaLock, FaEnvelope, FaSpinner, FaExchangeAlt } from 'react-icons/fa'
import { login } from '../services/api'
import { useUser } from '../context/UserContext'
import Button from './common/Button'
import Input from './common/Input'
import FormGroup, { Label, ErrorMessage } from './common/FormGroup'
import Select from './common/Select'

const LoginContainer = styled.div`
  max-width: 400px;
  width: 100%;
`

const Form = styled.form`
  background: ${props => props.theme.colors.cardBackground};
  padding: ${props => props.theme.space.xl};
  border-radius: ${props => props.theme.borderRadius.md};
  box-shadow: ${props => props.theme.shadows.md};
  margin-bottom: 20px;
`

const FormTitle = styled.h2`
  text-align: center;
  margin-bottom: ${props => props.theme.space.lg};
  color: ${props => props.theme.colors.textPrimary};
`

const InputWrapper = styled.div`
  position: relative;
`

const Icon = styled.div`
  position: absolute;
  top: 50%;
  left: 12px;
  transform: translateY(-50%);
  color: ${props => props.theme.colors.textSecondary};
`

const StyledInput = styled(Input)`
  padding-left: 36px;
`

const Spinner = styled(FaSpinner)`
  animation: spin 1s linear infinite;

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`

const LoginForm: React.FC = () => {
  const { login: userLogin } = useUser()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    accountType: 'PRACTICE'
  })

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.email || !formData.password) {
      setError('Please enter both email and password')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await login(formData)

      if (response.success) {
        userLogin({
          email: formData.email,
          accountType: response.account_type,
          balance: response.balance
        })
      } else {
        setError(response.message || 'Login failed')
      }
    } catch (error) {
      setError(
        'Connection failed. Please check your internet connection or try again later.'
      )
      console.error('Login error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <LoginContainer>
      <Form onSubmit={handleSubmit}>
        <FormTitle>Login to IQ Option Trader</FormTitle>

        <FormGroup>
          <Label>Email</Label>
          <InputWrapper>
            <Icon>
              <FaEnvelope />
            </Icon>
            <StyledInput
              type='email'
              name='email'
              value={formData.email}
              onChange={handleChange}
              placeholder='Enter your email'
              fullWidth
              disabled={isLoading}
            />
          </InputWrapper>
        </FormGroup>

        <FormGroup>
          <Label>Password</Label>
          <InputWrapper>
            <Icon>
              <FaLock />
            </Icon>
            <StyledInput
              type='password'
              name='password'
              value={formData.password}
              onChange={handleChange}
              placeholder='Enter your password'
              fullWidth
              disabled={isLoading}
            />
          </InputWrapper>
        </FormGroup>

        <FormGroup>
          <Label>Account Type</Label>
          <InputWrapper>
            <Icon>
              <FaExchangeAlt />
            </Icon>
            <Select
              name='accountType'
              value={formData.accountType}
              onChange={handleChange}
              fullWidth
              disabled={isLoading}
            >
              <option value='PRACTICE'>Demo</option>
              <option value='REAL'>Real</option>
            </Select>
          </InputWrapper>
        </FormGroup>

        {error && <ErrorMessage>{error}</ErrorMessage>}

        <Button type='submit' fullWidth disabled={isLoading}>
          {isLoading ? (
            <>
              <Spinner /> Connecting...
            </>
          ) : (
            'Login'
          )}
        </Button>
      </Form>
    </LoginContainer>
  )
}

export default LoginForm
