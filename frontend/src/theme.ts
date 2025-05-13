import { DefaultTheme } from 'styled-components'

// Extend the default theme interface
declare module 'styled-components' {
  export interface DefaultTheme {
    md: string
    lg: string
    sm: string
    radius: {
      sm: string
      md: string
      lg: string
    }
    shadows: {
      sm: string
      md: string
      lg: string
    }
    colors: {
      cardBackground: string
      textPrimary: string
      textSecondary: string
      primary: string
      secondary: string
      background: string
      text: string
      success: string
      danger: string
      warning: string
    }
  }
}

// Define the theme with required properties
export const theme: DefaultTheme = {
  md: '768px', // Medium breakpoint for media queries
  lg: '1024px', // Large breakpoint
  sm: '576px', // Small breakpoint
  radius: {
    sm: '4px',
    md: '8px',
    lg: '16px'
  },
  shadows: {
    sm: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
    md: '0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23)',
    lg: '0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23)'
  },
  colors: {
    primary: '#007bff',
    secondary: '#6c757d',
    background: '#f8f9fa',
    text: '#212529',
    success: '#28a745',
    danger: '#dc3545',
    warning: '#ffc107',
    cardBackground: '#ffffff',
    textPrimary: '#212529',
    textSecondary: '#6c757d'
  },
  fonts: {
    main: ''
  }
}
