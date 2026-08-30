import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import AuthLayout from '../components/AuthLayout'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const { register, handleSubmit, formState: { isSubmitting } } = useForm()

  const onSubmit = async (data) => {
    setError('')
    try {
      await login(data.email, data.password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to continue chatting with your documents.">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm text-zinc-300">Email</label>
          <input type="email" className="input-field" {...register('email', { required: true })} />
        </div>
        <div>
          <label className="mb-1 block text-sm text-zinc-300">Password</label>
          <input type="password" className="input-field" {...register('password', { required: true })} />
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
          {isSubmitting ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-zinc-400">
        No account?{' '}
        <Link to="/register" className="font-medium text-brand-500 hover:text-brand-600">
          Create one
        </Link>
      </p>
    </AuthLayout>
  )
}
