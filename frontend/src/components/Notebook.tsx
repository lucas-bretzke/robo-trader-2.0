import React from 'react'
import styled from 'styled-components'
import { useNotebook } from '../context/NotebookContext'

interface NotebookProps {
  children: React.ReactNode
}

const NotebookContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: ${props => props.theme.colors.background};
  overflow: hidden;
`

const NotebookHeader = styled.div`
  height: 40px;
  background-color: ${props => props.theme.colors.primary};
  color: ${props => props.theme.colors.text};
  display: flex;
  align-items: center;
  padding: 0 20px;
  justify-content: space-between;
`

const NotebookBody = styled.div`
  display: flex;
  flex: 1;
  overflow: hidden;
`

const NotebookContent = styled.div`
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: ${props => props.theme.colors.cardBackground};
  display: flex;
  flex-direction: column;
  gap: 20px;
`

const TabsContainer = styled.div`
  display: flex;
  align-items: center;
`

const Tab = styled.div<{ active: boolean }>`
  padding: 8px 20px;
  cursor: pointer;
  border-top-left-radius: ${props => props.theme.borderRadius.sm};
  border-top-right-radius: ${props => props.theme.borderRadius.sm};
  font-weight: ${props => (props.active ? '600' : '400')};
  background-color: ${props =>
    props.active
      ? props.theme.colors.cardBackground
      : props.theme.colors.primary};
  color: ${props =>
    props.active ? props.theme.colors.primary : props.theme.colors.text};
  margin-right: 5px;
  transition: background-color 0.2s;

  &:hover {
    background-color: ${props =>
      props.active
        ? props.theme.colors.cardBackground
        : props.theme.colors.primaryLight};
  }
`

const NotebookTitle = styled.div`
  font-size: 16px;
  font-weight: bold;
`

const NotebookLines = styled.div`
  position: absolute;
  left: 0;
  top: 40px;
  bottom: 0;
  width: 30px;
  background-color: ${props => props.theme.colors.primary};
  border-right: 1px solid ${props => props.theme.colors.border};
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 20px;
`

const NotebookLine = styled.div`
  width: 20px;
  height: 1px;
  background-color: ${props => props.theme.colors.textSecondary};
  margin-bottom: 20px;
`

const Notebook: React.FC<NotebookProps> = ({ children }) => {
  const { activeTab, tabs, setActiveTab } = useNotebook()

  return (
    <NotebookContainer>
      <NotebookHeader>
        <NotebookTitle>IQ Option Trader Notebook</NotebookTitle>
        <TabsContainer>
          {tabs.map(tab => (
            <Tab
              key={tab.id}
              active={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.name}
            </Tab>
          ))}
        </TabsContainer>
      </NotebookHeader>
      <NotebookBody>
        <NotebookLines>
          {Array.from({ length: 20 }).map((_, index) => (
            <NotebookLine key={index} />
          ))}
        </NotebookLines>
        <NotebookContent>{children}</NotebookContent>
      </NotebookBody>
    </NotebookContainer>
  )
}

export default Notebook
