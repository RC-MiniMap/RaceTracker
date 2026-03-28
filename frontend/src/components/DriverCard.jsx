import { getTeamColor } from '../utils/teamColors'

function DriverCard({ position, driver_name, abbreviation, driver_number, team, lap_time, headshot_url, positionChange }) {
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
    </div>
  )
}

export default DriverCard
