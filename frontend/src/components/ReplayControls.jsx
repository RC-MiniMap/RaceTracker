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

  return (
    <div>
      <button onClick={onPlayPause} disabled={lapCount === 0}>
        {isPlaying ? 'Pause' : 'Play'}
      </button>

      <input
        type="range"
        min={0}
        max={lapCount > 0 ? lapCount - 1 : 0}
        value={currentLap}
        onChange={e => onScrub(Number(e.target.value))}
        disabled={lapCount === 0}
      />

      <span>Lap {lapNumber} / {totalLaps}</span>

      <select
        value={interval}
        onChange={e => onIntervalChange(Number(e.target.value))}
        disabled={lapCount === 0}
      >
        {speedOptions.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}

export default ReplayControls
