import { Plant, HEALTH_COLORS } from '@/types/garden'

interface Props {
  plant: Plant
  onClick?: () => void
  selected?: boolean
}

const GROWTH_LABELS: Record<Plant['growthStage'], string> = {
  seedling: 'ต้นกล้า', juvenile: 'เจริญเติบโต',
  mature: 'เต็มวัย', bearing: 'ออกผล', dormant: 'พักตัว',
}
const HEALTH_LABELS: Record<Plant['healthStatus'], string> = {
  healthy: 'สุขภาพดี', stressed: 'เครียด',
  diseased: 'ป่วย', critical: 'วิกฤต',
}

export default function PlantHealthCard({ plant, onClick, selected }: Props) {
  const color = HEALTH_COLORS[plant.healthStatus]
  return (
    <div
      onClick={onClick}
      className={`card cursor-pointer transition-all ${selected ? 'ring-2 ring-green-500' : 'hover:shadow-md'}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-800 text-sm">{plant.name}</h3>
          <p className="text-xs text-gray-500 mt-0.5">{plant.species} · {plant.variety}</p>
        </div>
        <div className="w-3 h-3 rounded-full mt-1" style={{ backgroundColor: color }} />
      </div>
      <div className="mt-2 flex gap-2">
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
          {GROWTH_LABELS[plant.growthStage]}
        </span>
        <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: color + '22', color }}>
          {HEALTH_LABELS[plant.healthStatus]}
        </span>
      </div>
    </div>
  )
}
