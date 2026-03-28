import DriverCard from './DriverCard'

function Leaderboard({ standings = [], currentLap, totalLaps, loading }) {
  if (loading) return <p>Loading...</p>

  return (
    <div>
      <h2>Lap {currentLap} / {totalLaps}</h2>
      <div>
        {standings.map(driver => (
          <DriverCard key={driver.driver_number} {...driver} />
        ))}
      </div>
    </div>
  )
}

export default Leaderboard
