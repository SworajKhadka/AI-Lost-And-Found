const FIELD_LABELS = {
  title: 'Title',
  description: 'Description',
  location: 'Location',
  contact: 'Contact',
  status: 'Status',
}

// Turn an axios error into a short message a user can act on.
export function getErrorMessage(err, fallback = 'Something went wrong. Please try again.') {
  if (!err?.response) {
    return 'Could not reach the server. Check your connection and try again.'
  }
  const { status, data } = err.response
  const detail = data?.detail

  // FastAPI validation errors: [{ loc: ['body', 'title'], msg: '...' }, ...]
  if (status === 422 && Array.isArray(detail) && detail.length) {
    const first = detail[0]
    const field = FIELD_LABELS[first.loc?.[first.loc.length - 1]] ?? 'Input'
    return `${field}: ${first.msg.replace(/^Value error, /, '')}`
  }
  if (typeof detail === 'string') return detail
  if (status >= 500) return 'The server had a problem. Please try again in a moment.'
  return fallback
}
