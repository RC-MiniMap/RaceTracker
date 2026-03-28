function DriverCard({ position, driver_name, abbreviation, driver_number, team, lap_time, headshot_url }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '8px 0', borderBottom: '1px solid #ccc' }}>
      <span style={{ width: '24px', fontWeight: 'bold' }}>{position}</span>
      {headshot_url
        ? <img src={headshot_url} alt={driver_name} style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover' }} />
        : <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#888' }} />
      }
      <span style={{ flex: 1 }}>{driver_name}</span>
      <span style={{ width: '36px', color: '#888' }}>{abbreviation}</span>
      <span style={{ width: '24px', color: '#888' }}>#{driver_number}</span>
      <span style={{ width: '140px', color: '#888' }}>{team}</span>
      <span style={{ width: '80px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{lap_time}</span>
    </div>
  )
}

export default DriverCard
