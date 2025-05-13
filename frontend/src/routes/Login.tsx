import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './Login.css'

const Login: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    // Check if user is already logged in
    const savedCredentials = localStorage.getItem('iqOptionCredentials')
    if (savedCredentials) {
      navigate('/dashboard')
    }
  }, [navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!email || !password) {
      setError('Por favor, preencha todos os campos.')
      return
    }

    setIsLoading(true)

    try {
      // Store credentials in localStorage
      localStorage.setItem(
        'iqOptionCredentials',
        JSON.stringify({ email, password })
      )

      // Navigate to dashboard
      navigate('/dashboard')
    } catch (err) {
      setError('Ocorreu um erro ao fazer login. Tente novamente.')
      console.error('Login error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className='login-container'>
      <div className='login-card'>
        <div className='login-header'>
          <h1>IQ Option Trader</h1>
          <p>Faça login com sua conta da IQ Option</p>
        </div>

        {error && <div className='error-message'>{error}</div>}

        <form onSubmit={handleSubmit} className='login-form'>
          <div className='form-group'>
            <label htmlFor='email'>Email</label>
            <input
              type='email'
              id='email'
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder='Seu email da IQ Option'
              required
            />
          </div>

          <div className='form-group'>
            <label htmlFor='password'>Senha</label>
            <input
              type='password'
              id='password'
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder='Sua senha da IQ Option'
              required
            />
          </div>

          <button type='submit' className='login-button' disabled={isLoading}>
            {isLoading ? 'Conectando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login
