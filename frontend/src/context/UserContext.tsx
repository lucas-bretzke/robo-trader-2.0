import React, { createContext, useContext, useState, ReactNode } from 'react'

interface User {
  id: string
  name: string
  email: string
  balance: number
  accountType: string
}

interface UserContextType {
  user: User
  isLoggedIn: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

// Default user
const defaultUser: User = {
  id: '1',
  name: 'Demo User',
  email: 'demo@example.com',
  balance: 1000,
  accountType: 'Demo'
}

const UserContext = createContext<UserContextType>({
  user: defaultUser,
  isLoggedIn: false,
  login: async () => {},
  logout: () => {}
})

export const UserProvider: React.FC<{ children: ReactNode }> = ({
  children
}) => {
  const [user, setUser] = useState<User>(defaultUser)
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  const login = async (email: string, password: string) => {
    // In a real app, you would make an API call here
    console.log('Logging in with:', email, password)
    setUser(defaultUser)
    setIsLoggedIn(true)
  }

  const logout = () => {
    setIsLoggedIn(false)
  }

  return (
    <UserContext.Provider
      value={{
        user,
        isLoggedIn,
        login,
        logout
      }}
    >
      {children}
    </UserContext.Provider>
  )
}

export const useUser = () => useContext(UserContext)
