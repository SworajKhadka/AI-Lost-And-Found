import { useState } from 'react'
import api from '../api/api'

const emptyForm = {
  title: '',
  description: '',
  status: 'lost',
  location: '',
  contact: '',
}

const requiredFields = ['title', 'description', 'location', 'contact']

const INPUT_BASE =
  'w-full bg-[#13110f] border rounded-lg px-4 py-2.5 text-sm text-[#f5f1ea] placeholder:text-[#6b6358] focus:outline-none focus:ring-2 transition-all'
const INPUT_NORMAL = `${INPUT_BASE} border-[#2e2822] focus:ring-[#f97316]/40 focus:border-[#f97316]/40`
const INPUT_ERROR  = `${INPUT_BASE} border-rose-500/50 focus:ring-rose-500/30 focus:border-rose-500/40`

export default function ItemForm({ onItemCreated }) {
  const [form, setForm]               = useState(emptyForm)
  const [fieldErrors, setFieldErrors] = useState({})
  const [submitError, setSubmitError] = useState('')
  const [success, setSuccess]         = useState(false)
  const [loading, setLoading]         = useState(false)

  function handleChange(e) {
    const { name, value } = e.target
    setForm({ ...form, [name]: value })
    if (fieldErrors[name]) setFieldErrors((p) => ({ ...p, [name]: false }))
  }

  function validate() {
    const errors = {}
    for (const field of requiredFields) {
      if (!form[field].trim()) errors[field] = true
    }
    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitError('')
    if (!validate()) return

    setLoading(true)
    try {
      const { data } = await api.post('/items/', form)
      onItemCreated(data)
      setForm(emptyForm)
      setFieldErrors({})
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch {
      setSubmitError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-[#1a1714] border border-[#2e2822] rounded-2xl p-6 space-y-4 shadow-xl shadow-black/40"
    >
      <h2 className="text-lg font-semibold text-[#f5f1ea]">Report an Item</h2>

      {/* Lost / Found toggle */}
      <div className="flex gap-1 p-1 bg-[#13110f] rounded-full border border-[#2e2822]">
        {['lost', 'found'].map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setForm({ ...form, status: s })}
            className={`flex-1 py-1.5 rounded-full text-sm font-medium capitalize transition-all ${
              form.status === s
                ? 'bg-gradient-to-r from-[#f97316] to-[#ea580c] text-[#0e0c0a] shadow-lg shadow-[#f97316]/20'
                : 'text-[#d4c5a8]/60 hover:text-[#d4c5a8]'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Title */}
      <div className="space-y-1">
        <input
          name="title"
          value={form.title}
          onChange={handleChange}
          placeholder="Title (e.g. Blue AirPods case)"
          className={fieldErrors.title ? INPUT_ERROR : INPUT_NORMAL}
        />
        {fieldErrors.title && (
          <p className="text-rose-400 text-xs pl-1">Title is required.</p>
        )}
      </div>

      {/* Description */}
      <div className="space-y-1">
        <textarea
          name="description"
          value={form.description}
          onChange={handleChange}
          placeholder="Description — be specific, Gemini uses this to auto-tag the item"
          rows={3}
          className={`${fieldErrors.description ? INPUT_ERROR : INPUT_NORMAL} resize-none`}
        />
        {fieldErrors.description && (
          <p className="text-rose-400 text-xs pl-1">Description is required.</p>
        )}
      </div>

      {/* Location */}
      <div className="space-y-1">
        <input
          name="location"
          value={form.location}
          onChange={handleChange}
          placeholder="Location (e.g. Library 2nd floor)"
          className={fieldErrors.location ? INPUT_ERROR : INPUT_NORMAL}
        />
        {fieldErrors.location && (
          <p className="text-rose-400 text-xs pl-1">Location is required.</p>
        )}
      </div>

      {/* Contact */}
      <div className="space-y-1">
        <input
          name="contact"
          value={form.contact}
          onChange={handleChange}
          placeholder="Contact (email or phone)"
          className={fieldErrors.contact ? INPUT_ERROR : INPUT_NORMAL}
        />
        {fieldErrors.contact && (
          <p className="text-rose-400 text-xs pl-1">Contact is required.</p>
        )}
      </div>

      {/* Backend error */}
      {submitError && (
        <p className="text-rose-400 text-sm bg-rose-500/10 border border-rose-500/20 rounded-lg px-4 py-2">
          {submitError}
        </p>
      )}

      {/* Success banner */}
      {success && (
        <p className="text-emerald-400 text-sm bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-4 py-2">
          Item reported successfully!
        </p>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-[#f97316] hover:bg-[#ea580c] disabled:opacity-50 disabled:cursor-not-allowed text-[#0e0c0a] font-semibold py-2.5 rounded-xl text-sm hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg shadow-[#f97316]/20"
      >
        {loading ? 'Submitting…' : 'Submit Item'}
      </button>
    </form>
  )
}
