import { useState, useEffect } from 'react'

function useDriverRatings(year, round, lapNumber) {
  const [ratings, setRatings] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!year || !round || !lapNumber) {
      setRatings(null)
      return
    }

    setLoading(true)
    setError(null)

    fetch(`/api/race/${year}/${round}/driver-ratings?lap=${lapNumber}`)
      .then(async res => {
        if (!res.ok) {
          let errorMessage = `Request failed with status ${res.status}`
          try {
            const errorData = await res.json()
            if (errorData && typeof errorData.error === 'string') {
              errorMessage = errorData.error
            }
          } catch (e) {
            // Ignore JSON parse errors
          }
          throw new Error(errorMessage)
        }
        return res.json()
      })
      .then(data => {
        setRatings(data.ratings || {})
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setRatings(null)
        setLoading(false)
      })
  }, [year, round, lapNumber])

  return { ratings, loading, error }
}

export default useDriverRatings
