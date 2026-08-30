import { motion } from 'framer-motion'
import { FiFileText } from 'react-icons/fi'

export default function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-zinc-950 to-zinc-900">
      <div className="mx-auto flex min-h-screen max-w-6xl items-center justify-center px-4 py-12">
        <div className="grid w-full gap-8 lg:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="hidden flex-col justify-center lg:flex"
          >
            <div className="mb-6 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600/20 text-brand-500">
              <FiFileText size={28} />
            </div>
            <h1 className="text-4xl font-bold tracking-tight text-white">VectorDoc</h1>
            <p className="mt-4 max-w-md text-lg text-zinc-300">
              Upload PDFs, ask questions, and get accurate answers grounded in your documents using semantic search and Ollama.
            </p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="card mx-auto w-full max-w-md">
            <h2 className="text-2xl font-semibold text-white">{title}</h2>
            {subtitle && <p className="mt-2 text-sm text-zinc-400">{subtitle}</p>}
            <div className="mt-6">{children}</div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
