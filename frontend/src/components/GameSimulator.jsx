import { useState } from 'react'

// Lightweight at-bat simulator that mirrors the logic in the backend
// (baseball_manager_ai/simulation/game_simulator.py) so the UI works even
// before models are wired in.

const OUTCOME_ORDER = ['strikeout', 'walk', 'single', 'double', 'triple', 'home_run', 'out']

function simulateAtBat(batter, pitcher) {
  const batterOps = batter.ops ?? 0.75
  const batterK = batter.kRate ?? 0.215
  const batterBB = batter.bbRate ?? 0.085
  const pitcherEra = pitcher.era ?? 4.0

  const pitcherQuality = pitcherEra > 0 ? 4.0 / pitcherEra : 1.0
  const batterQuality = batterOps > 0 ? batterOps / 0.75 : 1.0

  let kProb = Math.min(0.40, batterK * pitcherQuality)
  let bbProb = Math.min(0.15, batterBB * batterQuality)
  const contactProb = 1 - kProb
  const avg = batter.avg ?? 0.26
  const contactHitRate = contactProb > 0 ? avg / contactProb : 0.3
  let hitProb = contactProb * contactHitRate

  const total = kProb + bbProb + hitProb
  if (total > 1) {
    kProb /= total; bbProb /= total; hitProb /= total
  }
  const outProb = 1 - kProb - bbProb - hitProb

  const r = Math.random()
  if (r < kProb) return 'strikeout'
  if (r < kProb + bbProb) return 'walk'
  if (r < kProb + bbProb + hitProb) {
    const hitR = Math.random()
    if (hitR < 0.65) return 'single'
    if (hitR < 0.85) return 'double'
    if (hitR < 0.95) return 'triple'
    return 'home_run'
  }
  return 'out'
}

function simulateGame(home, away, homeLineup, awayLineup, homePitcher, awayPitcher, maxInnings = 9) {
  let homeScore = 0
  let awayScore = 0
  let inning = 1
  const log = []

  while (inning <= maxInnings) {
    const awayRuns = simulateHalfInning(away, awayLineup, homePitcher)
    awayScore += awayRuns

    if (inning < maxInnings || awayScore > homeScore) {
      const homeRuns = simulateHalfInning(home, homeLineup, awayPitcher)
      homeScore += homeRuns
    }

    log.push({ inning, away: awayRuns, home: homeRuns })
    inning++
  }

  return { homeScore, awayScore, log }
}

function simulateHalfInning(team, lineup, pitcher) {
  let runs = 0
  let outs = 0
  const bases = [false, false, false]
  let batterIndex = 0

  while (outs < 3) {
    const batter = lineup[batterIndex % lineup.length]
    batterIndex++
    const outcome = simulateAtBat(batter, pitcher)

    if (outcome === 'strikeout' || outcome === 'out') {
      outs++
    } else if (outcome === 'walk') {
      if (bases.every(Boolean)) runs++
      bases[2] = bases[1]; bases[1] = bases[0]; bases[0] = true
    } else if (outcome === 'home_run') {
      runs += 1 + bases.filter(Boolean).length
      for (let i = 0; i < 3; i++) bases[i] = false
    } else {
      const advance = { single: 1, double: 2, triple: 3 }[outcome]
      for (let i = 2; i >= 0; i--) {
        if (bases[i]) {
          if (i + advance >= 3) runs++
          else bases[i + advance] = true
          bases[i] = false
        }
      }
      if (advance < 3) bases[advance - 1] = true
      else runs++
    }
  }
  return runs
}

export default function GameSimulator() {
  const [homeTeam, setHomeTeam] = useState('NYY')
  const [awayTeam, setAwayTeam] = useState('BOS')
  const [simResult, setSimResult] = useState(null)
  const [simLog, setSimLog] = useState(null)

  const teams = ['NYY', 'BOS', 'LAD', 'SF', 'HOU', 'TEX', 'SEA', 'ATL', 'PHI', 'CHC', 'TOR', 'BAL']

  const lineupFor = (team) => Array(9).fill(null).map((_, i) => ({
    id: `${team}_${i}`,
    name: `${team} Batter ${i + 1}`,
    ops: +(0.65 + Math.random() * 0.2).toFixed(3),
    kRate: 0.18 + Math.random() * 0.08,
    bbRate: 0.06 + Math.random() * 0.06,
    avg: +(0.22 + Math.random() * 0.08).toFixed(3),
  }))

  const handleSimulate = () => {
    const homeLineup = lineupFor(homeTeam)
    const awayLineup = lineupFor(awayTeam)
    const homePitcher = { era: 3.5, k9: 8.5 }
    const awayPitcher = { era: 4.2, k9: 7.8 }

    const result = simulateGame(
      homeTeam, awayTeam, homeLineup, awayLineup,
      homePitcher, awayPitcher
    )
    setSimResult(result)
    setSimLog(result.log)
  }

  return (
    <div className="card">
      <h2>Game Simulator</h2>
      <p className="hint">Runs a Monte Carlo–style simulation from batter &amp; pitcher stats.</p>

      <div className="team-picker">
        <div className="team-select">
          <label>Away</label>
          <select value={awayTeam} onChange={(e) => setAwayTeam(e.target.value)}>
            {teams.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div className="vs">VS</div>
        <div className="team-select">
          <label>Home</label>
          <select value={homeTeam} onChange={(e) => setHomeTeam(e.target.value)}>
            {teams.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      <button className="primary-btn" onClick={handleSimulate}>Simulate Game</button>

      {simResult && (
        <div className="sim-result">
          <div className="scoreboard">
            <div className="score-cell">
              <span className="team-name">{awayTeam}</span>
              <span className="score">{simResult.awayScore}</span>
            </div>
            <div className="score-cell">
              <span className="team-name">{homeTeam}</span>
              <span className="score">{simResult.homeScore}</span>
            </div>
          </div>

          {simLog && (
            <div className="inning-log">
              {simLog.map((inning, i) => (
                <div key={i} className="inning-row">
                  <span className="inning-num">{i + 1}</span>
                  <span className="inning-away">{inning.away}</span>
                  <span className="inning-home">{inning.home}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
