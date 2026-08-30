import { useState } from 'react'
import Navbar from '../components/Navbar'
import DocumentPanel from '../components/DocumentPanel'
import ChatPanel from '../components/ChatPanel'

export default function DashboardPage() {
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([])
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div className="min-h-screen bg-black">
      <Navbar />
      <main className="mx-auto grid max-w-[1600px] gap-5 px-4 py-5 lg:grid-cols-[300px_minmax(0,1fr)] sm:px-6">
        <DocumentPanel
          selectedIds={selectedDocumentIds}
          onSelectionChange={setSelectedDocumentIds}
          refreshKey={refreshKey}
        />
        <ChatPanel
          selectedDocumentIds={selectedDocumentIds}
          onDocumentsChanged={() => setRefreshKey((key) => key + 1)}
        />
      </main>
    </div>
  )
}
