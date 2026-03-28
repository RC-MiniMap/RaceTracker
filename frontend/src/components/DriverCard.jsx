import { getTeamColor } from '../utils/teamColors'

function getRatingColor(rating) {
  if (rating >= 8.0) return '#4ade80'  // green — excellent
  if (rating >= 7.0) return '#a3e635'  // lime — good
  if (rating >= 6.0) return '#facc15'  // yellow — average
  if (rating >= 5.0) return '#fb923c'  // orange — below average
  return '#ef4444'                      // red — poor
}

function DriverCard({ position, driver_name, abbreviation, driver_number, team, lap_time, headshot_url, positionChange, rating }) {
  const teamColor = getTeamColor(team)

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      height: 'var(--row-height)',
      padding: '0 12px',
      borderBottom: '1px solid var(--border)',
      backgroundColor: 'var(--bg-surface)',
      transition: 'background 0.15s',
    }}
    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.04)'}
    onMouseLeave={e => e.currentTarget.style.background = 'var(--bg-surface)'}
    >
      <div style={{ width: '36px', display: 'flex', alignItems: 'center', gap: '4px' }}>
        <span style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-bright)' }}>{position}</span>
        {positionChange !== 0 && (
          <span style={{ fontSize: '11px', fontWeight: 600, color: positionChange > 0 ? '#4ade80' : '#ef4444' }}>
            {positionChange > 0 ? '▲' : '▼'}{Math.abs(positionChange)}
          </span>
        )}
      </div>

      <div style={{
        width: '4px',
        height: '60%',
        background: teamColor,
        borderRadius: '2px',
        margin: '0 10px',
      }} />

      <div style={{ display: 'flex', alignItems: 'center', flex: 1, gap: '6px' }}>
        <span style={{ fontWeight: 700, fontSize: '15px', letterSpacing: '0.5px', color: 'var(--text-bright)', width: '40px' }}>
          {abbreviation}
        </span>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          {driver_name}
        </span>
      </div>

      <span style={{ fontSize: '12px', color: 'var(--text-muted)', width: '50px' }}>
        #{driver_number}
      </span>

      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text)', textAlign: 'right', width: '80px', fontVariantNumeric: 'tabular-nums' }}>
        {lap_time}
      </span>

      {rating != null ? (
        <div style={{
          width: '52px',
          textAlign: 'center',
          marginLeft: '8px',
        }}>
          <span style={{
            display: 'inline-block',
            minWidth: '36px',
            padding: '2px 6px',
            borderRadius: '4px',
            fontSize: '13px',
            fontWeight: 700,
            fontFamily: 'var(--font-mono)',
            fontVariantNumeric: 'tabular-nums',
            color: '#111',
            background: getRatingColor(rating.overall_rating),
            opacity: rating.is_provisional ? 0.6 : 1,
          }}>
            {rating.overall_rating.toFixed(1)}
          </span>
        </div>
      ) : (
        <div style={{ width: '52px', marginLeft: '8px' }} />
      )}
    </div>
  )
}

export default DriverCard
