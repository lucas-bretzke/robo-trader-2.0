import 'styled-components'

declare module 'styled-components' {
  export interface DefaultTheme {
    colors: {
      primary: string
      secondary: string
      success: string
      danger: string
      warning: string
      info: string // Adicionado info explicitamente
      light: string
      dark: string
      cardBackground: string
      textPrimary: string
      textSecondary: string
      background: string
      text: string
    }
    spacing: {
      xs: string
      sm: string
      md: string
      lg: string
      xl: string
    }
    fontSize: {
      xs: string
      sm: string
      md: string
      lg: string
      xl: string
    }
    borderRadius: {
      sm: string
      md: string
      lg: string
      round: string
    }
    // Para compatibilidade com o código existente
    sm: string
    md: string
    lg: string
    radius: string
    shadows: {
      small: string
      medium: string
      large: string
    }
  }
}
