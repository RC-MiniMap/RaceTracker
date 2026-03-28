const FIXED_SPEED_OPTIONS = [
  { label: '1s',  value: 1000  },
  { label: '3s',  value: 3000  },
  { label: '5s',  value: 5000  },
  { label: '10s', value: 10000 },
  { label: '15s', value: 15000 },
  { label: '30s', value: 30000 },
  { label: '1min', value: 60000 },
]

function ReplayControls({ currentLap, lapCount, lapNumber, totalLaps, isPlaying, onPlayPause, onScrub, interval, onIntervalChange, avgLapTimeMs }) {
  const speedOptions = avgLapTimeMs
    ? [...FIXED_SPEED_OPTIONS, { label: 'Avg lap time', value: avgLapTimeMs }]
    : FIXED_SPEED_OPTIONS

  const playButtonStyle = {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    background: 'var(--accent)',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '18px',
    fontWeight: 'bold',
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '16px',
      padding: '12px 24px',
      background: 'inherit',
    }}>
      <button onClick={onPlayPause} disabled={lapCount === 0} style={playButtonStyle}>
        {isPlaying ? '⏸' : '▶'}
      </button>

      <input
        type="range"
        min={0}
        max={lapCount > 0 ? lapCount - 1 : 0}
        value={currentLap}
        onChange={e => onScrub(Number(e.target.value))}
        disabled={lapCount === 0}
        style={{
          flex: 1,
          WebkitAppearance: 'none',
          appearance: 'none',
          height: '4px',
          background: 'var(--border)',
          borderRadius: '2px',
          outline: 'none',
          cursor: 'pointer',
        }}
      />

      <style>{`
        input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 14px;
          height: 14px;
          border-radius: 50%;
          background: white;
          cursor: pointer;
          box-shadow: 0 0 4px rgba(0,0,0,0.4);
        }
        input[type="range"]::-moz-range-thumb {
          width: 14px;
          height: 14px;
          border-radius: 50%;
          background: white;
          cursor: pointer;
          border: none;
          box-shadow: 0 0 4px rgba(0,0,0,0.4);
        }
      `}</style>

      <span style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', color: 'var(--text)', whiteSpace: 'nowrap' }}>
        Lap {lapNumber}/{totalLaps}
      </span>

      <select
        value={interval}
        onChange={e => onIntervalChange(Number(e.target.value))}
        disabled={lapCount === 0}
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
        {speedOptions.map(opt => (
          <option key={`${opt.label}-${opt.value}`} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}

export default ReplayControls
