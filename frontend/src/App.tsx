import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Sidebar } from '@/components/Sidebar'
import { Header } from '@/components/Header'
import { Home } from '@/pages/Home'
import { EmpresaDetalle } from '@/pages/EmpresaDetalle'
import { ScoreDesglose } from '@/pages/ScoreDesglose'
import { ApiExplorer } from '@/pages/ApiExplorer'
import { Bitacora } from '@/pages/Bitacora'

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <>
    <Sidebar />
    <Header />
    <main
      className="min-h-screen bg-surface-container-low"
      style={{ marginLeft: 240, marginTop: 56, padding: 24 }}
    >
      {children}
    </main>
  </>
)

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <Layout>
              <Home />
            </Layout>
          }
        />
        <Route
          path="/empresas/:nit"
          element={
            <Layout>
              <EmpresaDetalle />
            </Layout>
          }
        />
        <Route
          path="/empresas/:nit/score/:indicador"
          element={
            <Layout>
              <ScoreDesglose />
            </Layout>
          }
        />
        <Route
          path="/api-explorer"
          element={
            <Layout>
              <ApiExplorer />
            </Layout>
          }
        />
        <Route
          path="/bitacora"
          element={
            <Layout>
              <Bitacora />
            </Layout>
          }
        />
        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
