import { Link } from 'react-router-dom'
import { FiLogOut, FiMessageSquare } from 'react-icons/fi'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()

  return (
    <header className="border-b border-zinc-800 bg-black/90 backdrop-blur">
      <div className="mx-auto flex max-w-[1600px] items-center justify-between px-4 py-3 sm:px-6">
        <Link to="/" className="flex items-center gap-3 text-base font-semibold text-white">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-zinc-700 bg-zinc-800 text-zinc-100 shadow-lg shadow-black/30"><FiMessageSquare /></span>
          <span>VectorDoc</span>
        </Link>
        <div className="flex items-center gap-3">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium text-white">{user?.full_name}</p>
            <p className="text-xs capitalize text-zinc-400">{user?.role}</p>
          </div>
          <button onClick={logout} className="icon-button w-auto gap-2 px-3" title="Log out">
            <FiLogOut />
            <span className="hidden sm:inline">Log out</span>
          </button>
        </div>
      </div>
    </header>
  )
}
