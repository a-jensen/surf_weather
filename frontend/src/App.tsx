import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Header } from './components/layout/Header'
import { LakeListPage } from './components/lake-list/LakeListPage'
import { LakeDetailPage } from './components/lake-detail/LakeDetailPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="max-w-5xl mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<LakeListPage />} />
            <Route path="/lakes/:id" element={<LakeDetailPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
