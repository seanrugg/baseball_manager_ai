import { useState, useEffect } from 'react'
import GamePredictor from './components/GamePredictor'
import GameSimulator from './components/GameSimulator'
import { checkHealth } from './api/client'

export default function App() {
  const [health, setHealth] = useState(null)
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    checkHealth()
      .then((h) => {
        setHealth(h)
        setStatus(h.database === 'connected' ? 'connected' : 'disconnected')
      })
      .catch(() => setStatus('unreachable'))
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">⚾</span>
          <div>
            <h1>Baseball Manager AI</h1>
            <p className="tagline">AI-powered lineup &amp; in-game decision support</p>
          </div>
        </div>

        <div className={`status-badge status-${status}`}>
          <span className="dot" />
          {status === 'connected' && 'Backend connected'}
          {status === 'unreachable' && 'Backend unreachable'}
          {status === 'disconnected' && 'Backend disconnected'}
          {status === 'checking' && 'Checking...'}
        </div>
      </header>

      <nav className="tabs">
        <button className="tab active">Game Predictor</button>
        <button className="tab">Game Simulator</button>
      </nav>

      <main className="app-main">
        <GamePredictor />
        <GameSimulator />
      </main>

      <footer className="app-footer">
        {health && (
          <span>
            Models loaded: <strong>{health.models_loaded}</strong>
          </span>
        )}
        <span>FastAPI · Python</span>
      </footer>
    </div>
  )
}
