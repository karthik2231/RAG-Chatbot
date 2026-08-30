import { useCallback, useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { FiTrash2, FiUpload } from 'react-icons/fi'
import { documentsApi } from '../api/client'

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function DocumentPanel({ selectedIds, onSelectionChange, refreshKey }) {
  const [documents, setDocuments] = useState([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  const loadDocuments = useCallback(async () => {
    const { data } = await documentsApi.list()
    setDocuments(data)
  }, [])

  useEffect(() => {
    loadDocuments().catch(() => setError('Failed to load documents'))
  }, [loadDocuments, refreshKey])

  const handleUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    setError('')
    try {
      await documentsApi.upload(file)
      await loadDocuments()
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const handleDelete = async (id) => {
    await documentsApi.delete(id)
    onSelectionChange(selectedIds.filter((docId) => docId !== id))
    await loadDocuments()
  }

  const toggleSelection = (id) => {
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((docId) => docId !== id))
    } else {
      onSelectionChange([...selectedIds, id])
    }
  }

  return (
    <div className="card flex min-h-[360px] flex-col lg:min-h-[calc(100vh-5.5rem)]">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white">Documents</h2>
          <p className="mt-0.5 text-xs text-zinc-400">Select PDFs to focus your chat</p>
        </div>
        <button onClick={() => fileInputRef.current?.click()} disabled={uploading} className="btn-primary gap-2 rounded-xl px-3 text-xs">
          <FiUpload />
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
        <input ref={fileInputRef} type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
      </div>

      {error && <p className="mb-3 text-sm text-zinc-300">{error}</p>}

      <div className="flex-1 space-y-2 overflow-y-auto pr-1">
        {documents.length === 0 ? (
          <p className="rounded-lg border border-dashed border-zinc-700 p-6 text-center text-sm text-zinc-400">
            No documents yet. Upload a PDF to get started.
          </p>
        ) : (
          documents.map((doc) => (
            <motion.div
              key={doc.id}
              layout
              className={`rounded-xl border p-3 transition ${
                selectedIds.includes(doc.id)
                  ? 'border-zinc-500 bg-zinc-800'
                  : 'border-zinc-800 bg-black hover:border-zinc-700'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <button onClick={() => toggleSelection(doc.id)} className="flex-1 text-left">
                  <p className="truncate text-sm font-medium text-white">{doc.original_filename}</p>
                  <p className="mt-1 text-xs text-zinc-400">
                    {formatBytes(doc.file_size)} · {doc.page_count} pages · {doc.chunk_count} chunks
                  </p>
                  <span
                    className={`mt-2 inline-block rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide ${
                      doc.status === 'ready'
                        ? 'bg-emerald-500/10 text-emerald-400'
                        : doc.status === 'failed'
                          ? 'bg-red-500/10 text-red-400'
                          : 'bg-amber-500/10 text-amber-400'
                    }`}
                  >
                    {doc.status}
                  </span>
                </button>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="rounded-md p-2 text-zinc-400 transition hover:bg-zinc-800 hover:text-zinc-100"
                >
                  <FiTrash2 size={16} />
                </button>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  )
}
