import { supabase } from '../../lib/supabaseClient'

export const LogoutButton = () => {
  const handleLogout = async () => {
    await supabase.auth.signOut()
  }

  return <button onClick={handleLogout}>Logout</button>
}
