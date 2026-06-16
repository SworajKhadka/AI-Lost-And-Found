import { useState } from 'react'
import api from '../api/api'
import MatchResults from './MatchResults'

const STATUS_STYLES = {
  lost:  'bg-orange-950/40 text-[#f97316] border border-[#f97316]/25 shadow-[0_0_8px_rgba(249,115,22,0.15)]',
  found: 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/25 shadow-[0_0_8px_rgba(52,211,153,0.12)]',
}

function staggerClass(index) {
  return `stagger-${Math.min(index, 9)}`
}

export default function ItemList({ items, loading, tokenMap, onItemDeleted }) {
  const [matchData,    setMatchData]    = useState(null)
  const [matchLoading, setMatchLoading] = useState(null)
  const [deleteLoading,setDeleteLoading]= useState(null)

  async function handleFindMatches(item) {
    setMatchLoading(item.id)
    try {
      const { data } = await api.post('/matches/', { item_id: item.id })
      setMatchData(data)
    } catch (err) {
      console.error('Match request failed:', err)
      alert('Could not fetch matches. Make sure the backend is running.')
    } finally {
      setMatchLoading(null)
    }
  }

  async function handleDelete(item) {
    if (!window.confirm(`Delete "${item.title}"? This cannot be undone.`)) return

    const token = tokenMap[item.id]
    if (!token) return

    setDeleteLoading(item.id)
    try {
      await api.delete(`/items/${item.id}`, {
        headers: { 'X-Owner-Token': token },
      })
      onItemDeleted(item.id)
    } catch (err) {
      console.error('Delete failed:', err)
      const msg = err.response?.status === 403
        ? 'You do not have permission to delete this item.'
        : 'Could not delete item. Make sure the backend is running.'
      alert(msg)
    } finally {
      setDeleteLoading(null)
    }
  }

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-[#1a1714] border border-[#2e2822] rounded-2xl p-5 h-32 animate-pulse" />
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <p className="text-[#9c9388]/40 text-sm text-center py-12">
        No items yet. Be the first to report one!
      </p>
    )
  }

  return (
    <>
      <div className="space-y-3">
        {items.map((item, index) => {
          const isOwner = Boolean(tokenMap[item.id])

          return (
            <div
              key={item.id}
              className={`animate-fade-up ${staggerClass(index)} bg-[#1a1714] border border-[#2e2822] rounded-2xl p-5 flex flex-col gap-2.5 hover:border-[#f97316]/30 hover:shadow-lg hover:shadow-[#f97316]/[0.06] transition-all`}
            >
              {/* Top row: title + status badge */}
              <div className="flex items-start justify-between gap-3">
                <h3 className="font-semibold text-[#f5f1ea] text-base leading-snug">
                  {item.title}
                </h3>
                <span
                  className={`text-xs font-medium px-2.5 py-0.5 rounded-full capitalize shrink-0 ${
                    STATUS_STYLES[item.status] ?? 'bg-[#2e2822] text-[#9c9388] border border-[#2e2822]'
                  }`}
                >
                  {item.status}
                </span>
              </div>

              {/* Description */}
              <p className="text-[#9c9388] text-sm leading-relaxed">{item.description}</p>

              {/* Gemini tags */}
              <div className="flex flex-wrap gap-1.5">
                {item.category && (
                  <span className="bg-[#f97316]/10 text-[#f97316] border border-[#f97316]/20 text-xs px-2.5 py-0.5 rounded-full">
                    {item.category}
                  </span>
                )}
                {(item.keywords ?? []).map((kw) => (
                  <span
                    key={kw}
                    className="bg-[#d4c5a8]/10 text-[#d4c5a8] border border-[#d4c5a8]/15 text-xs px-2.5 py-0.5 rounded-full"
                  >
                    {kw}
                  </span>
                ))}
              </div>

              {/* Location + contact */}
              <div className="flex flex-wrap gap-x-5 text-xs text-[#9c9388]/60">
                <span>📍 {item.location}</span>
                <span>✉️ {item.contact}</span>
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-5 pt-0.5">
                <button
                  onClick={() => handleFindMatches(item)}
                  disabled={matchLoading === item.id || deleteLoading === item.id}
                  className="group flex items-center gap-1.5 text-sm text-[#f97316] hover:text-[#ea580c] disabled:opacity-40 transition-colors"
                >
                  <span>🔍</span>
                  <span className="group-hover:underline underline-offset-2">
                    {matchLoading === item.id ? 'Finding matches…' : 'Find Matches'}
                  </span>
                </button>

                {/* Only rendered for items this session created */}
                {isOwner && (
                  <button
                    onClick={() => handleDelete(item)}
                    disabled={deleteLoading === item.id || matchLoading === item.id}
                    className="group flex items-center gap-1.5 text-sm text-[#9c9388]/50 hover:text-rose-500/80 disabled:opacity-40 transition-colors"
                  >
                    <span>✓</span>
                    <span className="group-hover:underline underline-offset-2">
                      {deleteLoading === item.id ? 'Removing…' : 'Mark as Resolved'}
                    </span>
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Match results modal */}
      {matchData !== null && (
        <MatchResults
          matches={matchData}
          onClose={() => setMatchData(null)}
        />
      )}
    </>
  )
}
