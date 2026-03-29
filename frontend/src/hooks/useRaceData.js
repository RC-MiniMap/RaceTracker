import { useState, useEffect } from 'react'

function useRaceData(year, round) {
  const [raceData, setRaceData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!year || !round) return

    setLoading(true)
    setError(null)

    fetch(`/api/race/${year}/${round}/laps`)
      .then(async res => {
        if (!res.ok) {
          let errorMessage = `Request failed with status ${res.status}`
          try {
            const errorData = await res.json()
            if (errorData && typeof errorData.error === 'string') {
              errorMessage = errorData.error
            }
          } catch (e) {
            // Ignore JSON parse errors and fall back to generic message
          }
          throw new Error(errorMessage)
        }
        return res.json()
      })
      .then(data => {
        setRaceData(data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [year, round])

  return { raceData, loading, error }
}

export default useRaceData
