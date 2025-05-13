import React, { createContext, useContext, useState, ReactNode } from 'react'

type TabType = 'controls' | 'chart' | 'history'

interface NotebookContextType {
  activeTab: TabType
  setActiveTab: (tab: TabType) => void
}

const NotebookContext = createContext<NotebookContextType>({
  activeTab: 'controls',
  setActiveTab: () => {}
})

export const NotebookProvider: React.FC<{ children: ReactNode }> = ({
  children
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('controls')

  return (
    <NotebookContext.Provider
      value={{
        activeTab,
        setActiveTab
      }}
    >
      {children}
    </NotebookContext.Provider>
  )
}

export const useNotebook = () => useContext(NotebookContext)
