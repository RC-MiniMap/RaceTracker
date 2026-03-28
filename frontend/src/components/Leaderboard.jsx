import DriverCard from './DriverCard'

function Leaderboard({ standings = [], currentLap, totalLaps, loading, raceData, currentLapIndex, ratings }) {
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <div style={{
          width: '32px',
          height: '32px',
          border: '3px solid var(--border)',
          borderTopColor: 'var(--accent)',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
      </div>
    )
  }

  const previousStandings = raceData?.laps?.[currentLapIndex - 1]?.standings || []
  const positionMap = {}
  previousStandings.forEach(driver => {
    positionMap[driver.driver_number] = driver.position
  })

  return (
    <div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        fontSize: '13px',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '2px',
        color: 'var(--text-muted)',
        borderBottom: '1px solid var(--border)',
      }}>
        <span>LAP {currentLap} / {totalLaps}</span>
        {ratings && <span style={{ fontSize: '11px', letterSpacing: '1px' }}>RATING</span>}
      </div>
      <div>
        {standings.map(driver => {
          const prevPos = positionMap[driver.driver_number]
          const positionChange = prevPos ? prevPos - driver.position : 0
          const driverRating = ratings?.[driver.abbreviation] || null
          return (
            <DriverCard
              key={driver.driver_number}
              {...driver}
              positionChange={positionChange}
              rating={driverRating}
            />
          )
        })}
      </div>
    </div>
  )
}

export default Leaderboard
