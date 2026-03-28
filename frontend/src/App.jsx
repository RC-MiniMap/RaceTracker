import { useState } from 'react'
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
  const [currentLap] = useState(0)
  const { raceData, loading } = useRaceData(2024, 1)

  const standings = raceData?.laps[currentLap]?.standings ?? STUB_STANDINGS
  const totalLaps = raceData?.total_laps ?? '—'
  const lapNumber = raceData?.laps[currentLap]?.lap_number ?? currentLap + 1

  return (
    <div>
      <RaceSelector />
      <Leaderboard
        standings={standings}
        currentLap={lapNumber}
        totalLaps={totalLaps}
        loading={loading}
      />
      <ReplayControls />
    </div>
  )
}

export default App
