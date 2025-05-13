import styled from 'styled-components'

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
`

export const Label = styled.label`
  font-size: 0.9rem;
  margin-bottom: 6px;
  color: ${props => props.theme.colors.textSecondary};
  font-weight: 500;
`

export const ErrorMessage = styled.span`
  color: ${props => props.theme.colors.danger};
  font-size: 0.8rem;
  margin-top: 4px;
`

export default FormGroup
