import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../../lib/supabaseClient'
import { clearExtensionAuth } from '../../lib/extensionAuth'

export const Logout = () => {
  const navigate = useNavigate()

  useEffect(() => {
    const doLogout = async () => {
      await clearExtensionAuth()
      await supabase.auth.signOut()
      navigate('/', { replace: true })
    }
    void doLogout()
  }, [navigate])

  return null
}



