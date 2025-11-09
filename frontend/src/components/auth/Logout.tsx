import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { clearExtensionAuth } from '../../lib/extensionAuth'

export const Logout = () => {
  const navigate = useNavigate()
  const { signOut } = useAuth()

  useEffect(() => {
    const doLogout = async () => {
      await clearExtensionAuth()
      await signOut()
      navigate('/', { replace: true })
    }
    void doLogout()
  }, [navigate, signOut])

  return null
}
