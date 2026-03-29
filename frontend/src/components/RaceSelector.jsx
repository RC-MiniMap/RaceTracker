import { useState, useEffect } from 'react'

function RaceSelector({ onRaceSelect }) {
  const [races, setRaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedValue, setSelectedValue] = useState('')

  useEffect(() => {
    fetch('/api/races')
      .then(res => {
        if (!res.ok) throw new Error(`Failed to fetch races (${res.status})`)
        return res.json()
      })
      .then(data => {
        if (!Array.isArray(data)) throw new Error('Invalid response format')
        // Sort by date descending so the most recent past race is first
        const sorted = [...data].sort((a, b) => (b.date || '').localeCompare(a.date || ''))
        setRaces(data)
        setLoading(false)
        if (sorted.length > 0) {
          const latest = sorted[0]
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
