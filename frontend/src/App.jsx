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
  const currentLapData = raceData?.laps?.[currentLap]
  const standings = currentLapData?.standings ?? STUB_STANDINGS
  const totalLaps = raceData?.total_laps ?? '—'
  const lapNumber = currentLapData?.lap_number ?? currentLap + 1

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
    if (!isPlaying || lapCount < 2) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
      return
    }

    intervalRef.current = setInterval(() => {
      setCurrentLap(prev => {
        const upperBound = Math.max(0, lapCount - 1)
        const next = prev + 1
        if (next >= upperBound) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current)
          }
          setIsPlaying(false)
          return upperBound
        }
        return next
      })
    }, replayInterval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isPlaying, lapCount, replayInterval])

  useEffect(() => {
    if (lapCount <= 0) {
      setCurrentLap(0)
      return
    }
    setCurrentLap(prev => {
      if (prev < 0) return 0
      if (prev >= lapCount) return lapCount - 1
      return prev
    })
  }, [lapCount])

  const handlePlayPause = () => {
    if (!raceData || lapCount < 2) return
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
