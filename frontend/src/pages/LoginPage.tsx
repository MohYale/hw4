import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../api.ts'
import { useAuth } from '../auth.tsx'

export function LoginPage() {
  const navigate = useNavigate()
  const { setShopper } = useAuth()
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setBusy(true)
    setNote('')
    try {
      const shopper = await login(
        String(form.get('email') ?? ''),
        String(form.get('password') ?? ''),
        String(form.get('size') ?? ''),
      )
      setShopper(shopper)
      navigate('/')
    } catch (reason: unknown) {
      setNote(reason instanceof Error ? reason.message : 'Could not log in')
      setBusy(false)
    }
  }

  return (
    <div className="page narrow">
      <p className="eyebrow">Log in</p>
      <h1>Welcome back to the shop.</h1>
      <p className="page-note">
        Use the email on your Campus Customs account. Need one?{' '}
        <Link to="/create-account">Create an account</Link>.
      </p>
      <form className="account-form" onSubmit={onSubmit}>
        <label>
          Email
          <input type="email" name="email" autoComplete="email" required />
        </label>
        <label>
          Password
          <input type="password" name="password" autoComplete="current-password" required />
        </label>
        <label>
          Your size
          <select name="size" defaultValue="">
            <option value="">No size preference</option>
            <option value="XS">Extra small</option>
            <option value="S">Small</option>
            <option value="M">Medium</option>
            <option value="L">Large</option>
            <option value="XL">Extra large</option>
            <option value="XXL">XXL</option>
          </select>
        </label>
        <p className="page-note">
          The size you choose is saved on the account. The catalogue then opens on
          pieces that still have that size in stock.{' '}
          <Link to="/forgot-password">Forgot your password?</Link>
        </p>
        <button className="button" type="submit" disabled={busy}>
          {busy ? 'Logging in…' : 'Log in'}
        </button>
        {note ? <p className="form-note">{note}</p> : null}
      </form>
    </div>
  )
}
