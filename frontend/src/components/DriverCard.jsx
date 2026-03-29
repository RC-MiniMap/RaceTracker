import { getTeamColor } from '../utils/teamColors'

function getRatingColor(rating) {
  if (rating >= 8.0) return '#4ade80'  // green — excellent
  if (rating >= 7.0) return '#a3e635'  // lime — good
  if (rating >= 6.0) return '#facc15'  // yellow — average
  if (rating >= 5.0) return '#fb923c'  // orange — below average
  return '#ef4444'                      // red — poor
}

/** Map a category score (-2 to +2) to a 0-100% bar width. */
function scoreToPercent(score) {
  // Clamp to -2..+2, then scale to 0..100
  const clamped = Math.max(-2, Math.min(2, score))
  return ((clamped + 2) / 4) * 100
}

/** Map a category score to a color. */
function getScoreColor(score) {
  if (score >= 1.0) return '#4ade80'
  if (score >= 0.3) return '#a3e635'
  if (score >= -0.3) return '#facc15'
  if (score >= -1.0) return '#fb923c'
  return '#ef4444'
}

const CATEGORIES = [
  { key: 'pace',            label: 'Pace' },
  { key: 'racecraft',       label: 'Racecraft' },
  { key: 'execution',       label: 'Execution' },
  { key: 'position_impact', label: 'Position' },
  { key: 'discipline',      label: 'Discipline' },
]

function RatingBreakdown({ rating }) {
  return (
    <div style={{
      padding: '8px 12px 12px',
      borderBottom: '1px solid var(--border)',
      background: 'rgba(0,0,0,0.25)',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '10px',
      }}>
        <span style={{
          fontSize: '11px',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '1.5px',
          color: 'var(--text-muted)',
        }}>
          Rating Breakdown
        </span>
        {rating.is_provisional && (
          <span style={{
            fontSize: '10px',
            fontWeight: 600,
            color: '#fb923c',
            textTransform: 'uppercase',
            letterSpacing: '1px',
          }}>
            Provisional
          </span>
        )}
      </div>
      {CATEGORIES.map(({ key, label }) => {
        const score = rating[key] ?? 0
        const pct = scoreToPercent(score)
        const color = getScoreColor(score)
        return (
          <div key={key} style={{ marginBottom: '6px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '2px',
            }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>
                {label}
              </span>
              <span style={{
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                fontVariantNumeric: 'tabular-nums',
                color: color,
                fontWeight: 700,
              }}>
                {score > 0 ? '+' : ''}{score.toFixed(2)}
              </span>
            </div>
            <div style={{
              height: '4px',
              background: 'rgba(255,255,255,0.08)',
              borderRadius: '2px',
              overflow: 'hidden',
            }}>
              <div style={{
                height: '100%',
                width: `${pct}%`,
                background: color,
                borderRadius: '2px',
                transition: 'width 0.3s ease',
              }} />
            </div>
          </div>
        )
      })}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: '10px',
        paddingTop: '8px',
        borderTop: '1px solid var(--border)',
      }}>
        <span style={{
          fontSize: '12px',
          fontWeight: 700,
          color: 'var(--text-bright)',
          textTransform: 'uppercase',
          letterSpacing: '1px',
        }}>
          Overall
        </span>
        <span style={{
          fontSize: '16px',
          fontWeight: 700,
          fontFamily: 'var(--font-mono)',
          color: getRatingColor(rating.overall_rating),
        }}>
          {rating.overall_rating.toFixed(1)}
        </span>
      </div>
    </div>
  )
}

function DriverCard({ position, driver_name, abbreviation, driver_number, team, lap_time, headshot_url, positionChange, rating, expanded, onRatingClick }) {
  const teamColor = getTeamColor(team)

  return (
    <div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        height: 'var(--row-height)',
        padding: '0 12px',
        borderBottom: expanded ? 'none' : '1px solid var(--border)',
        backgroundColor: expanded ? 'rgba(255,255,255,0.03)' : 'var(--bg-surface)',
        transition: 'background 0.15s',
      }}
      onMouseEnter={e => { if (!expanded) e.currentTarget.style.background = 'rgba(255,255,255,0.04)' }}
      onMouseLeave={e => { if (!expanded) e.currentTarget.style.background = 'var(--bg-surface)' }}
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

        {headshot_url ? (
          <img
            src={headshot_url}
            alt={abbreviation}
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              objectFit: 'cover',
              marginRight: '6px',
              background: 'rgba(255,255,255,0.08)',
            }}
          />
        ) : (
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            background: 'rgba(255,255,255,0.08)',
            marginRight: '6px',
          }} />
        )}

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
          <div
            style={{
              width: '52px',
              textAlign: 'center',
              marginLeft: '8px',
              cursor: 'pointer',
            }}
            onClick={() => onRatingClick(abbreviation)}
            title="Click to see rating breakdown"
          >
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
              outline: expanded ? '2px solid var(--text-bright)' : 'none',
              outlineOffset: '1px',
              transition: 'outline 0.15s',
            }}>
              {rating.overall_rating.toFixed(1)}
            </span>
          </div>
        ) : (
          <div style={{ width: '52px', marginLeft: '8px' }} />
        )}
      </div>

      {expanded && rating && (
        <RatingBreakdown rating={rating} />
      )}
    </div>
  )
}

export default DriverCard
