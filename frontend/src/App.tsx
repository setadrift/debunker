import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import Home from "./pages/Home";
import Login from "./pages/Login";
import NarrativeDetail from "./pages/NarrativeDetail";
import GraphPage from './pages/Graph';
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
                  <Route path="/narratives/:id" element={<NarrativeDetail />} />
                  <Route path="/graph" element={<GraphPage />} />
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
