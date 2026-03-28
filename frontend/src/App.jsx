import { useState, useEffect, useRef } from 'react'
import './App.css'
import RaceSelector from './components/RaceSelector'
import Leaderboard from './components/Leaderboard'
import ReplayControls from './components/ReplayControls'
import useRaceData from './hooks/useRaceData'

const STUB_STANDINGS = [
  { position: 1, driver_name: 'Max Verstappen', abbreviation: 'VER', driver_number: 1, team: 'Red Bull Racing', lap_time: '1:34.523', headshot_url: '' },
  { position: 2, driver_name: 'Charles Leclerc', abbreviation: 'LEC', driver_number: 16, team: 'Ferrari', lap_time: '1:34.891', headshot_url: '' },
  { position: 3, driver_name: 'Carlos Sainz', abbreviation: 'SAI', driver_number: 55, team: 'Ferrari', lap_time: '1:35.012', headshot_url: '' },
  { position: 4, driver_name: 'Sergio Perez', abbreviation: 'PER', driver_number: 11, team: 'Red Bull Racing', lap_time: '1:35.210', headshot_url: '' },
  { position: 5, driver_name: 'Lando Norris', abbreviation: 'NOR', driver_number: 4, team: 'McLaren', lap_time: '1:35.450', headshot_url: '' },
]

function App() {
  const [currentLap, setCurrentLap] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [replayInterval, setReplayInterval] = useState(5000)
  const intervalRef = useRef(null)
  const { raceData, loading } = useRaceData(2024, 1)

  const lapCount = raceData?.laps?.length ?? 0
  const standings = raceData?.laps[currentLap]?.standings ?? STUB_STANDINGS
  const totalLaps = raceData?.total_laps ?? '—'
  const lapNumber = raceData?.laps[currentLap]?.lap_number ?? currentLap + 1

  const avgLapTimeMs = raceData ? (() => {
    const times = raceData.laps.flatMap(lap =>
      lap.standings
        .filter(s => s.position === 1 && s.lap_time)
        .map(s => {
          const [mins, secs] = s.lap_time.split(':')
          return Number(mins) * 60000 + Number(secs) * 1000
        })
    ).filter(t => !isNaN(t))
    return times.length ? Math.round(times.reduce((a, b) => a + b, 0) / times.length) : null
  })() : null

  useEffect(() => {
    if (!isPlaying) return

    intervalRef.current = setInterval(() => {
      setCurrentLap(prev => {
        const next = prev + 1
        if (next >= lapCount - 1) {
          clearInterval(intervalRef.current)
          setIsPlaying(false)
          return lapCount - 1
        }
        return next
      })
    }, replayInterval)

    return () => clearInterval(intervalRef.current)
  }, [isPlaying, lapCount, replayInterval])

  const handlePlayPause = () => {
    if (!raceData) return
    setIsPlaying(prev => !prev)
  }

  const handleScrub = (lapIndex) => {
    setCurrentLap(lapIndex)
    setIsPlaying(false)
  }

  return (
    <div>
      <RaceSelector />
      <Leaderboard
        standings={standings}
        currentLap={lapNumber}
        totalLaps={totalLaps}
        loading={loading}
      />
      <ReplayControls
        currentLap={currentLap}
        lapCount={lapCount}
        lapNumber={lapNumber}
        totalLaps={totalLaps}
        isPlaying={isPlaying}
        onPlayPause={handlePlayPause}
        onScrub={handleScrub}
        interval={replayInterval}
        onIntervalChange={setReplayInterval}
        avgLapTimeMs={avgLapTimeMs}
      />
    </div>
  )
}

export default App
