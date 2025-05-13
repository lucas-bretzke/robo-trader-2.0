import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { StyleSheetManager, ThemeProvider } from 'styled-components'
import isPropValid from '@emotion/is-prop-valid'
import theme from './styles/theme'
import GlobalStyles from './styles/GlobalStyles'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <StyleSheetManager shouldForwardProp={prop => isPropValid(prop)}>
      <ThemeProvider theme={theme}>
        <GlobalStyles />
        <App />
      </ThemeProvider>
    </StyleSheetManager>
  </React.StrictMode>
)
