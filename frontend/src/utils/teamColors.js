export const TEAM_COLORS = {
  'Red Bull Racing': '#3671C6',
  'Ferrari': '#E8002D',
  'McLaren': '#FF8000',
  'Mercedes': '#27F4D2',
  'Aston Martin': '#229971',
  'Alpine': '#FF87BC',
  'Williams': '#64C4FF',
  'AlphaTauri': '#6692FF',
  'RB': '#6692FF',
  'Alfa Romeo': '#C92D4B',
  'Kick Sauber': '#52E252',
  'Haas F1 Team': '#B6BABD',
}

export function getTeamColor(teamName) {
  return TEAM_COLORS[teamName] ?? '#888888'
}
