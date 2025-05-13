import React from 'react'
import { UserProvider } from './context/UserContext'
import { NotebookProvider } from './context/NotebookContext'
import { RobotProvider } from './context/RobotContext'
import Dashboard from './components/Dashboard'

const App: React.FC = () => {
  return (
    <UserProvider>
      <NotebookProvider>
        <RobotProvider>
          <Dashboard />
        </RobotProvider>
      </NotebookProvider>
    </UserProvider>
  )
}

export default App
