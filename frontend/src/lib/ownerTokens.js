// Owner tokens prove that this browser created an item and may delete it.
// They used to live in sessionStorage, which is wiped when the tab closes —
// after that nobody could ever mark their own item as resolved.
// localStorage keeps them across visits on the same device.

const STORAGE_KEY = 'laf_owner_tokens'

function read(storage) {
  try {
    return JSON.parse(storage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

export function loadTokenMap() {
  const persisted = read(window.localStorage)
  // One-time migration of tokens saved by the previous sessionStorage version
  const legacy = read(window.sessionStorage)
  if (Object.keys(legacy).length) {
    const merged = { ...legacy, ...persisted }
    saveTokenMap(merged)
    try { window.sessionStorage.removeItem(STORAGE_KEY) } catch { /* ignore */ }
    return merged
  }
  return persisted
}

export function saveTokenMap(map) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(map))
  } catch {
    // Storage can be unavailable (private mode / quota); deleting just won't persist
  }
}
