import { useState } from 'react'
import { predictGame, getStrategy } from '../api/client'

export default function GamePredictor() {
  const [homeTeam, setHomeTeam] = useState('NYY')
  const [awayTeam, setAwayTeam] = useState('BOS')
  const [result, setResult] = useState(null)
  const [strategy, setStrategy] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const teams = [
    'NYY', 'BOS', 'LAD', 'SF', 'HOU', 'TEX', 'SEA', 'LAN',
    'ATL', 'MIA', 'PHI', 'NYM', 'CHC', 'CIN', 'STL', 'MIL',
    'DET', 'MIN', 'CLE', 'KC', 'CHW', 'TOR', 'BAL', 'TB',
    'NYM', 'WSH', 'COL', 'ARI', 'SD', 'OAK', 'LAA',
  ]

  const handlePredict = async () => {
    setLoading(true)
    setError(null)
    try {
      const lineup = Array(9).fill(null).map((_, i) => `player_${i}`)
      const prediction = await predictGame({
        home_team: homeTeam,
        away_team: awayTeam,
        lineup_home: lineup,
        lineup_away: lineup,
        starting_pitchers: { home: 'SP1', away: 'SP2' },
      })

      const strat = await getStrategy({
        game_situation: {
          inning: 8,
          outs: 1,
          score_differential: Math.round(
            (prediction.home_win_probability - 0.5) * 10
          ),
        },
        available_strategies: ['steal', 'bunt', 'hit_and_run'],
      })

      setResult(prediction)
      setStrategy(strat)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Game Predictor</h2>

      <div className="team-picker">
        <div className="team-select">
          <label>Away</label>
          <select value={awayTeam} onChange={(e) => setAwayTeam(e.target.value)}>
            {teams.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div className="vs">VS</div>

        <div className="team-select">
          <label>Home</label>
          <select value={homeTeam} onChange={(e) => setHomeTeam(e.target.value)}>
            {teams.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div>

      <button
        className="primary-btn"
        onClick={handlePredict}
        disabled={loading}
      >
        {loading ? 'Calculating...' : 'Predict Game'}
      </button>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="results">
          <div className="prob-bars">
            <div className="prob-row">
              <span className="prob-label">{homeTeam} Win</span>
              <div className="bar-track">
                <div
                  className="bar-fill home"
                  style={{ width: `${(result.home_win_probability * 100).toFixed(0)}%` }}
                />
              </div>
              <span className="prob-value">
                {(result.home_win_probability * 100).toFixed(1)}%
              </span>
            </div>
            <div className="prob-row">
              <span className="prob-label">{awayTeam} Win</span>
              <div className="bar-track">
                <div
                  className="bar-fill away"
                  style={{ width: `${(result.away_win_probability * 100).toFixed(0)}%` }}
                />
              </div>
              <span className="prob-value">
                {(result.away_win_probability * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="stat-grid">
            <div className="stat">
              <span className="stat-value">{result.expected_runs_home.toFixed(1)}</span>
              <span className="stat-key">Expected Runs ({homeTeam})</span>
            </div>
            <div className="stat">
              <span className="stat-value">{result.expected_runs_away.toFixed(1)}</span>
              <span className="stat-key">Expected Runs ({awayTeam})</span>
            </div>
            <div className="stat">
              <span className="stat-value">{(result.confidence * 100).toFixed(0)}%</span>
              <span className="stat-key">Confidence</span>
            </div>
          </div>

          {strategy && (
            <div className="strategy-result">
              <h3>Strategy Recommendation</h3>
              <p className="recommended">
                {strategy.recommended_strategy.replace(/_/g, ' ')}
                <span className="success-prob">
                  {(strategy.success_probability * 100).toFixed(0)}% success
                </span>
              </p>
              <ul className="alternatives">
                {strategy.alternative_strategies.map((alt, i) => (
                  <li key={i}>
                    {alt.strategy.replace(/_/g, ' ')} —{' '}
                    {(alt.success_probability * 100).toFixed(0)}%
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
