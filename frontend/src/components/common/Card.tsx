import styled from 'styled-components'

interface CardProps {
  padding?: string
  elevation?: 'low' | 'medium' | 'high'
}

const Card = styled.div<CardProps>`
  background-color: ${props => props.theme.colors.cardBackground};
  border-radius: ${props => props.theme.borderRadius.md};
  padding: ${props => props.padding || props.theme.space.lg};
  box-shadow: ${props => {
    switch (props.elevation) {
      case 'low':
        return props.theme.shadows.sm
      case 'high':
        return props.theme.shadows.lg
      default:
        return props.theme.shadows.md
    }
  }};
`

Card.defaultProps = {
  elevation: 'medium'
}

export default Card
