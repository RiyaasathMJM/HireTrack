// ── App.tsx ───────────────────────────────────────────────────────────────────

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Candidates from './pages/Candidates';
import CandidateDetail from './pages/CandidateDetail';
import Jobs from './pages/Jobs';
import Upload from './pages/Upload';

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'var(--surface)',
            color: 'var(--text)',
            border: '1px solid var(--border)',
            borderRadius: '10px',
            fontSize: '14px',
          },
        }}
      />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/"              element={<Dashboard />} />
          <Route path="/candidates"    element={<Candidates />} />
          <Route path="/candidates/:id" element={<CandidateDetail />} />
          <Route path="/jobs"          element={<Jobs />} />
          <Route path="/upload"        element={<Upload />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
