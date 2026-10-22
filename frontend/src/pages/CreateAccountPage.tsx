import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createAccount } from '../api.ts'
import { useAuth } from '../auth.tsx'

export function CreateAccountPage() {
  const navigate = useNavigate()
  const { setShopper } = useAuth()
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const password = String(form.get('password') ?? '')
    const confirmPassword = String(form.get('confirmPassword') ?? '')
    if (password !== confirmPassword) {
      setNote('Those passwords do not match.')
      return
    }
    setBusy(true)
    setNote('')
    try {
      const shopper = await createAccount({
        first_name: String(form.get('firstName') ?? ''),
        last_name: String(form.get('lastName') ?? ''),
        email: String(form.get('email') ?? ''),
        password,
        confirm_password: confirmPassword,
      })
      setShopper(shopper)
      navigate('/')
    } catch (reason: unknown) {
      setNote(reason instanceof Error ? reason.message : 'Could not create the account')
      setBusy(false)
    }
  }

  return (
    <div className="page narrow">
      <p className="eyebrow">Create account</p>
      <h1>Keep a name with the shop.</h1>
      <p className="page-note">
        Already have an account? <Link to="/login">Log in</Link>.
      </p>
      <form className="account-form" onSubmit={onSubmit}>
        <label>
          First name
          <input type="text" name="firstName" autoComplete="given-name" required />
        </label>
        <label>
          Last name
          <input type="text" name="lastName" autoComplete="family-name" required />
        </label>
        <label>
          Email
          <input type="email" name="email" autoComplete="email" required />
        </label>
        <label>
          Password
          <input
            type="password"
            name="password"
            autoComplete="new-password"
            minLength={8}
            required
          />
        </label>
        <label>
          Confirm password
          <input
            type="password"
            name="confirmPassword"
            autoComplete="new-password"
            minLength={8}
            required
          />
        </label>
        <button className="button" type="submit" disabled={busy}>
          {busy ? 'Creating account…' : 'Create account'}
        </button>
        {note ? <p className="form-note">{note}</p> : null}
      </form>
    </div>
  )
}
