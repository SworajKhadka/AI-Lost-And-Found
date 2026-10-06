import { useEffect, useState } from 'react'
import api from './api/api'
import ItemForm from './components/ItemForm'
import ItemList from './components/ItemList'
import { getErrorMessage } from './lib/errors'
import { loadTokenMap, saveTokenMap } from './lib/ownerTokens'

export default function App() {
  const [items,       setItems]       = useState([])
  const [loadingItems,setLoadingItems]= useState(true)
  const [loadError,   setLoadError]   = useState('')
  const [tokenMap,    setTokenMap]    = useState(loadTokenMap)

  // Bumped by the "Try again" button to re-run the load effect
  const [reloadKey,   setReloadKey]   = useState(0)

  useEffect(() => {
    let cancelled = false
    async function fetchItems() {
      try {
        const { data } = await api.get('/items/')
        if (cancelled) return
        setItems([...data].reverse()) // API returns oldest first; show newest first
        setLoadError('')
      } catch (err) {
        if (!cancelled) setLoadError(getErrorMessage(err, 'Could not load items.'))
      } finally {
        if (!cancelled) setLoadingItems(false)
      }
    }
    fetchItems()
    return () => { cancelled = true }
  }, [reloadKey])

  function handleRetry() {
    setLoadingItems(true)
    setLoadError('')
    setReloadKey((k) => k + 1)
  }

  function handleItemCreated(newItem) {
    const { owner_token, ...itemWithoutToken } = newItem
    setItems((prev) => [itemWithoutToken, ...prev])
    if (owner_token) {
      const updated = { ...tokenMap, [newItem.id]: owner_token }
      setTokenMap(updated)
      saveTokenMap(updated)
    }
  }

  function handleItemDeleted(deletedId) {
    setItems((prev) => prev.filter((item) => item.id !== deletedId))
    const rest = { ...tokenMap }
    delete rest[deletedId]
    setTokenMap(rest)
    saveTokenMap(rest)
  }

  return (
    <div className="min-h-screen bg-[#0e0c0a] text-[#f5f1ea]">

      {/* Ambient warm glow blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[420px] bg-[#f97316]/[0.06] rounded-full blur-3xl" />
        <div className="absolute top-[65vh] -right-40 w-[420px] h-[420px] bg-[#f97316]/[0.03] rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative border-b border-[#2e2822] bg-[#1a1714]/70 backdrop-blur-sm">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_90%_150%_at_50%_-10%,rgba(249,115,22,0.05),transparent)]" />
        <div className="relative max-w-2xl mx-auto px-6 py-6">
          <h1 className="text-3xl font-extrabold tracking-tight text-[#f5f1ea]">
            AI Lost & Found
          </h1>
          <p className="text-[#9c9388] text-sm mt-1.5">
            Report a lost or found item — Gemini automatically tags and matches it
          </p>
        </div>
      </header>

      {/* Main content */}
      <main className="relative max-w-2xl mx-auto px-4 py-8 space-y-8">
        <ItemForm onItemCreated={handleItemCreated} />

        <section>
          <p className="text-xs font-semibold text-[#9c9388]/50 uppercase tracking-widest mb-4">
            All Items ({items.length})
          </p>
          {loadError ? (
            <div role="alert" className="bg-[#1a1714] border border-rose-500/20 rounded-2xl p-6 text-center space-y-3">
              <p className="text-rose-400 text-sm">{loadError}</p>
              <button
                onClick={handleRetry}
                className="text-sm text-[#f97316] hover:text-[#ea580c] underline underline-offset-2"
              >
                Try again
              </button>
            </div>
          ) : (
          <ItemList
            items={items}
            loading={loadingItems}
            tokenMap={tokenMap}
            onItemDeleted={handleItemDeleted}
          />
          )}
        </section>
      </main>
    </div>
  )
}
