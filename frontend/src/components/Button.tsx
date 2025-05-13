import styled from 'styled-components'

// Define button types
type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'success'
  | 'danger'
  | 'warning'
  | 'info'

interface ButtonProps {
  $variant?: ButtonVariant
  $fullWidth?: boolean
}

const Button = styled.button<ButtonProps>`
  padding: ${({ theme }) => `${theme.spacing.sm} ${theme.spacing.md}`};
  font-size: ${({ theme }) => theme.fontSize.md};
  border-radius: ${({ theme }) => theme.borderRadius.sm};
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
  font-weight: 500;
  width: ${({ $fullWidth }) => ($fullWidth ? '100%' : 'auto')};

  /* Get button styles based on variant */
  background-color: ${({ theme, $variant = 'primary' }) => {
    return theme.colors[$variant as keyof typeof theme.colors]
  }};
  color: #fff;

  &:hover {
    opacity: 0.9;
  }

  &:active {
    transform: translateY(1px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`

// Add default props
Button.defaultProps = {
  $variant: 'primary',
  $fullWidth: false
}

export default Button
