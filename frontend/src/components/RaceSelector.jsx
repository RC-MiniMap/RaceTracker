import { useState, useEffect } from 'react'

function RaceSelector({ onRaceSelect }) {
  const [races, setRaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedValue, setSelectedValue] = useState('')

  useEffect(() => {
    fetch('/api/races')
      .then(res => res.json())
      .then(data => {
        setRaces(data)
        setLoading(false)
        if (data.length > 0) {
          const latest = data[data.length - 1]
          const value = `${latest.year}-${latest.round}`
          setSelectedValue(value)
          onRaceSelect(latest.year, latest.round)
        }
      })
      .catch(() => setLoading(false))
  }, [])

  const handleChange = (e) => {
    const value = e.target.value
    setSelectedValue(value)
    const [year, round] = value.split('-').map(Number)
    onRaceSelect(year, round)
  }

  if (loading) return <div>Loading races...</div>
  if (races.length === 0) return <div>No races available</div>

  return (
    <select value={selectedValue} onChange={handleChange}>
      {races.map(race => (
        <option key={`${race.year}-${race.round}`} value={`${race.year}-${race.round}`}>
          {race.year} {race.name}
        </option>
      ))}
    </select>
  )
}

export default RaceSelector
