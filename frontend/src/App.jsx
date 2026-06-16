import { useEffect, useState } from 'react'
import api from './api/api'
import ItemForm from './components/ItemForm'
import ItemList from './components/ItemList'

const TOKEN_STORAGE_KEY = 'laf_owner_tokens'

function loadTokenMap() {
  try { return JSON.parse(sessionStorage.getItem(TOKEN_STORAGE_KEY) || '{}') }
  catch { return {} }
}
function saveTokenMap(map) {
  sessionStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(map))
}

export default function App() {
  const [items,       setItems]       = useState([])
  const [loadingItems,setLoadingItems]= useState(true)
  const [tokenMap,    setTokenMap]    = useState(loadTokenMap)

  useEffect(() => {
    async function fetchItems() {
      try {
        const { data } = await api.get('/items/')
        setItems(data.reverse())
      } catch (err) {
        console.error('Failed to load items:', err)
      } finally {
        setLoadingItems(false)
      }
    }
    fetchItems()
  }, [])

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
          <ItemList
            items={items}
            loading={loadingItems}
            tokenMap={tokenMap}
            onItemDeleted={handleItemDeleted}
          />
        </section>
      </main>
    </div>
  )
}
