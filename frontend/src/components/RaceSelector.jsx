import { useState, useEffect } from 'react'

function RaceSelector({ onRaceSelect }) {
  const [races, setRaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedValue, setSelectedValue] = useState('')

  useEffect(() => {
    fetch('/api/races')
      .then(res => res.json())
      .then(data => {
        setRaces(data)
        setLoading(false)
        if (data.length > 0) {
          // Default to latest past race (future races have no lap data)
          const today = new Date()
          const pastRaces = data.filter(race => {
            if (!race.date) return true
            return new Date(race.date) <= today
          })
          const latest = pastRaces.length > 0 ? pastRaces[pastRaces.length - 1] : data[data.length - 1]
          const value = `${latest.year}-${latest.round}`
          setSelectedValue(value)
          onRaceSelect(latest.year, latest.round)
        }
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  const handleChange = (e) => {
    const value = e.target.value
    setSelectedValue(value)
    const [year, round] = value.split('-').map(Number)
    onRaceSelect(year, round)
  }

  if (loading) return <div>Loading races...</div>
  if (error) return <div>Failed to load races: {error}</div>
  if (races.length === 0) return <div>No races available</div>

  return (
    <select
      value={selectedValue}
      onChange={handleChange}
      style={{
        appearance: 'none',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        color: 'var(--text-bright)',
        padding: '6px 12px',
        borderRadius: '4px',
        cursor: 'pointer',
        fontSize: '13px',
      }}
    >
      {races.map(race => (
        <option key={`${race.year}-${race.round}`} value={`${race.year}-${race.round}`}>
          {race.year} {race.name}
        </option>
      ))}
    </select>
  )
}

export default RaceSelector
