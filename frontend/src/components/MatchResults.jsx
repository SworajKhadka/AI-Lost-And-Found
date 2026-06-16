function ScoreRing({ score }) {
  const r    = 17
  const circ = 2 * Math.PI * r
  const arc  = circ * (score / 100)

  const color =
    score >= 80 ? '#34d399' :   // emerald
    score >= 50 ? '#f97316' :   // orange
                  '#9c9388'     // muted beige-gray

  return (
    <svg width="44" height="44" viewBox="0 0 44 44" aria-label={`${score}% match`}>
      <circle cx="22" cy="22" r={r} fill="none" stroke="white" strokeOpacity="0.06" strokeWidth="3" />
      <circle
        cx="22" cy="22" r={r}
        fill="none"
        stroke={color}
        strokeWidth="3"
        strokeDasharray={`${arc} ${circ - arc}`}
        strokeLinecap="round"
        transform="rotate(-90 22 22)"
      />
      <text x="22" y="26" textAnchor="middle" fontSize="9" fontWeight="700" fill={color}>
        {score}%
      </text>
    </svg>
  )
}

function scoreLabelClass(score) {
  if (score >= 80) return 'text-emerald-400'
  if (score >= 50) return 'text-[#f97316]'
  return 'text-[#9c9388]'
}

function scoreLabel(score) {
  if (score >= 80) return 'Strong match'
  if (score >= 50) return 'Possible match'
  return 'Weak match'
}

export default function MatchResults({ matches, onClose }) {
  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      {/* Glass panel */}
      <div className="animate-scale-in bg-[#1a1714] border border-[#f97316]/20 rounded-2xl shadow-2xl shadow-black/60 w-full max-w-lg max-h-[80vh] flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#2e2822]">
          <h3 className="text-base font-semibold text-[#f5f1ea]">AI Match Results</h3>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-[#9c9388]/50 hover:text-[#f5f1ea] text-lg leading-none transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto px-6 py-4 space-y-3">
          {matches.length === 0 ? (
            <p className="text-[#9c9388]/40 text-sm text-center py-8">
              No matches found yet. More may appear as people report items.
            </p>
          ) : (
            matches.map((m) => (
              <div
                key={m.matched_item_id}
                className="bg-[#13110f] border border-[#2e2822] rounded-xl p-4 flex gap-4 items-start hover:border-[#f97316]/20 transition-colors"
              >
                {/* Score ring */}
                <ScoreRing score={m.match_score} />

                {/* Details */}
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-baseline justify-between gap-2">
                    <p className="font-semibold text-[#f5f1ea] text-sm truncate">{m.title}</p>
                    <span className={`text-xs font-semibold shrink-0 ${scoreLabelClass(m.match_score)}`}>
                      {scoreLabel(m.match_score)}
                    </span>
                  </div>
                  <p className="text-[#9c9388] text-xs leading-relaxed">{m.description}</p>
                  <div className="flex flex-wrap gap-x-4 text-xs text-[#9c9388]/60 pt-0.5">
                    <span>📍 {m.location}</span>
                    <span>✉️ {m.contact}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
