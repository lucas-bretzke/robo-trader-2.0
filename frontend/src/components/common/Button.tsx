import styled from 'styled-components'

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'warning' | 'success'

interface ButtonProps {
  variant?: ButtonVariant
  fullWidth?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const Button = styled.button<ButtonProps>`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;
  border-radius: ${props => props.theme.borderRadius.sm};
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;

  /* Size variants */
  padding: ${props =>
    props.size === 'sm'
      ? '6px 12px'
      : props.size === 'lg'
      ? '12px 24px'
      : '8px 16px'};

  font-size: ${props =>
    props.size === 'sm'
      ? '0.875rem'
      : props.size === 'lg'
      ? '1.125rem'
      : '1rem'};

  /* Color variants */
  background-color: ${props => {
    switch (props.variant) {
      case 'secondary':
        return props.theme.colors.secondary
      case 'danger':
        return props.theme.colors.danger
      case 'warning':
        return props.theme.colors.warning
      case 'success':
        return props.theme.colors.success
      default:
        return props.theme.colors.primary
    }
  }};

  color: white;

  /* Width */
  width: ${props => (props.fullWidth ? '100%' : 'auto')};

  &:hover:not(:disabled) {
    background-color: ${props => {
      switch (props.variant) {
        case 'secondary':
          return props.theme.colors.secondary
        case 'danger':
          return props.theme.colors.dangerHover
        case 'warning':
          return props.theme.colors.warningHover
        case 'success':
          return props.theme.colors.successHover
        default:
          return props.theme.colors.primaryHover
      }
    }};
    transform: translateY(-1px);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    background-color: ${props => props.theme.colors.disabled};
    cursor: not-allowed;
    opacity: 0.7;
  }
`

Button.defaultProps = {
  variant: 'primary',
  size: 'md',
  fullWidth: false
}

export default Button
