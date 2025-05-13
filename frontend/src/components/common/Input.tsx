import styled from 'styled-components'

interface InputProps {
  hasError?: boolean
  fullWidth?: boolean
}

const Input = styled.input<InputProps>`
  padding: 10px 12px;
  border: 1px solid
    ${props =>
      props.hasError ? props.theme.colors.danger : props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius.sm};
  background: ${props => props.theme.colors.inputBackground};
  color: ${props => props.theme.colors.text};
  font-size: 0.95rem;
  width: ${props => (props.fullWidth ? '100%' : 'auto')};

  &:focus {
    outline: none;
    border-color: ${props =>
      props.hasError ? props.theme.colors.danger : props.theme.colors.primary};
    box-shadow: 0 0 0 2px
      ${props =>
        props.hasError
          ? `${props.theme.colors.danger}30`
          : `${props.theme.colors.primary}30`};
  }

  &:disabled {
    background-color: ${props => props.theme.colors.disabled}30;
    cursor: not-allowed;
  }

  &::placeholder {
    color: ${props => props.theme.colors.textSecondary};
    opacity: 0.7;
  }
`

export default Input
