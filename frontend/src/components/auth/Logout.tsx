import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../../lib/supabaseClient'

export const Logout = () => {
  const navigate = useNavigate()

  useEffect(() => {
    const doLogout = async () => {
      await supabase.auth.signOut()
      navigate('/', { replace: true })
    }
    void doLogout()
  }, [navigate])

  return null
}



