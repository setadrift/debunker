import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import AuthGuard from "./components/AuthGuard";
import Home from "./pages/Home";
import Login from "./pages/Login";
import NarrativeDetail from "./pages/NarrativeDetail";
import GraphPage from './pages/Graph';
import BiasAnalysis from './pages/BiasAnalysis';
import './App.css'

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <div className="app-container">
          <Header />
          <div className="main-layout">
            <Sidebar />
            <main className="main-content">
              <div className="container">
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/narratives/:id" element={
                    <AuthGuard>
                      <NarrativeDetail />
                    </AuthGuard>
                  } />
                  <Route path="/graph" element={<GraphPage />} />
                  <Route path="/bias/:sourceId" element={<BiasAnalysis />} />
                </Routes>
              </div>
            </main>
          </div>
        </div>
      </Router>
    </ErrorBoundary>
  )
}

export default App
