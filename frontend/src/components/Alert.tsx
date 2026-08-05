import type { ReactNode } from 'react'
import './Alert.css'

type AlertProps = {
  type?: 'error' | 'warning' | 'success' | 'info'
  children: ReactNode
  className?: string
}

function Alert({ type = 'info', children, className = '' }: AlertProps) {
  return <p className={`alert alert-${type} ${className}`.trim()}>{children}</p>
}

export default Alert
