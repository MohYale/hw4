import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { resetPassword } from '../api.ts'

export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setBusy(true)
    setError('')
    try {
      await resetPassword(
        token,
        String(form.get('password') ?? ''),
        String(form.get('confirm_password') ?? ''),
      )
      setDone(true)
      setNote('Your password is updated. Log in with the new one.')
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : 'Could not update the password')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page narrow">
      <p className="eyebrow">New password</p>
      <h1>Choose a password for this account.</h1>
      {token ? (
        <form className="account-form" onSubmit={onSubmit}>
          <label>
            New password
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
              name="confirm_password"
              autoComplete="new-password"
              minLength={8}
              required
            />
          </label>
          <button className="button" type="submit" disabled={busy || done}>
            {busy ? 'Saving…' : 'Save password'}
          </button>
          {error ? <p className="form-note">{error}</p> : null}
          {note ? <p className="form-note">{note}</p> : null}
        </form>
      ) : (
        <p className="status error">That reset link is missing.</p>
      )}
      <p className="page-note">
        <Link to="/login">Log in</Link>
      </p>
    </div>
  )
}
