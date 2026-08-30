import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import AuthLayout from '../components/AuthLayout'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const { register: registerUser } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const { register, handleSubmit, formState: { isSubmitting } } = useForm()

  const onSubmit = async (data) => {
    setError('')
    try {
      await registerUser(data)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    }
  }

  return (
    <AuthLayout title="Create account" subtitle="Start uploading PDFs and chatting with your knowledge base.">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm text-zinc-300">Full name</label>
          <input className="input-field" {...register('full_name', { required: true, minLength: 2 })} />
        </div>
        <div>
          <label className="mb-1 block text-sm text-zinc-300">Email</label>
          <input type="email" className="input-field" {...register('email', { required: true })} />
        </div>
        <div>
          <label className="mb-1 block text-sm text-zinc-300">Password</label>
          <input type="password" className="input-field" {...register('password', { required: true, minLength: 8 })} />
        </div>
        {error && <p className="text-sm text-red-400">{typeof error === 'string' ? error : 'Registration failed'}</p>}
        <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
          {isSubmitting ? 'Creating account...' : 'Create account'}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-zinc-400">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-brand-500 hover:text-brand-600">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  )
}
