import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { requestPasswordReset } from '../api.ts'
import type { ResetNote } from '../api.ts'

export function ForgotPasswordPage() {
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [reset, setReset] = useState<ResetNote | null>(null)
  const [busy, setBusy] = useState(false)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setBusy(true)
    setError('')
    setReset(null)
    try {
      const prepared = await requestPasswordReset(String(form.get('email') ?? ''))
      setReset(prepared)
      setNote(prepared.message)
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : 'Could not prepare a reset link')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page narrow">
      <p className="eyebrow">Password</p>
      <h1>Set a new password.</h1>
      <p className="page-note">
        The shop stores a salted hash, so this email cannot contain your old
        password. The link lets you choose a new one. On this local shop the
        message is shown here as well as saved for your address.
      </p>
      <form className="account-form" onSubmit={onSubmit}>
        <label>
          Email
          <input type="email" name="email" autoComplete="email" required />
        </label>
        <button className="button" type="submit" disabled={busy}>
          {busy ? 'Preparing the link…' : 'Email a reset link'}
        </button>
        {error ? <p className="form-note">{error}</p> : null}
        {note ? <p className="form-note">{note}</p> : null}
      </form>
      {reset ? (
        <div className="email-preview">
          <p className="eyebrow">{reset.email_subject}</p>
          <pre>{reset.email_body}</pre>
          <Link className="button" to={reset.reset_path}>
            Open the reset link
          </Link>
        </div>
      ) : null}
      <p className="page-note">
        <Link to="/login">Back to log in</Link>
      </p>
    </div>
  )
}
