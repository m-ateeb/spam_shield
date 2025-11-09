import { useAuth } from '../../context/AuthContext'

export const LogoutButton = () => {
  const { signOut } = useAuth()

  const handleLogout = async () => {
    await signOut()
  }

  return <button onClick={handleLogout}>Logout</button>
}
