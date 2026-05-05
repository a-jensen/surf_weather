import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Header } from './components/layout/Header'
import { LakeListPage } from './components/lake-list/LakeListPage'
import { LakeDetailPage } from './components/lake-detail/LakeDetailPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <Header />
        <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<LakeListPage />} />
            <Route path="/lakes/:id" element={<LakeDetailPage />} />
          </Routes>
        </main>
        <footer className="text-center text-xs text-gray-400 py-4">
          © {new Date().getFullYear()} Austin Jensen
        </footer>
      </div>
    </BrowserRouter>
  )
}
