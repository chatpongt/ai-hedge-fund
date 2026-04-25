import { GardenActionPlan, GardenSignal } from '@/types/garden'
import { Droplets, Bug, Scissors, HeartPulse } from 'lucide-react'

interface Props {
  plan: GardenActionPlan
  selectedPlantId?: string
}

const SIGNAL_COLORS: Record<string, string> = {
  water_needed: 'text-blue-600 bg-blue-50',
  adequate: 'text-green-600 bg-green-50',
  over_watered: 'text-cyan-600 bg-cyan-50',
  pest_detected: 'text-red-600 bg-red-50',
  high_risk: 'text-orange-600 bg-orange-50',
  low_risk: 'text-green-600 bg-green-50',
  harvest_ready: 'text-yellow-600 bg-yellow-50',
  harvest_urgent: 'text-red-600 bg-red-50',
  not_ready: 'text-gray-600 bg-gray-50',
  treatment_needed: 'text-red-600 bg-red-50',
  disease_risk: 'text-orange-600 bg-orange-50',
  healthy: 'text-green-600 bg-green-50',
}

function SignalBadge({ signal }: { signal: string }) {
  const cls = SIGNAL_COLORS[signal] ?? 'text-gray-600 bg-gray-50'
  return <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cls}`}>{signal.replace(/_/g, ' ')}</span>
}

function AgentCard({ icon: Icon, label, signal }: { icon: React.ElementType; label: string; signal: GardenSignal }) {
  return (
    <div className="border border-gray-100 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-gray-400" />
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <div className="ml-auto">
          <SignalBadge signal={signal.signal} />
        </div>
      </div>
      <div className="flex items-center gap-2 mb-1">
        <div className="flex-1 bg-gray-100 rounded-full h-1.5">
          <div className="bg-green-500 h-1.5 rounded-full" style={{ width: `${signal.confidence}%` }} />
        </div>
        <span className="text-xs text-gray-500">{signal.confidence.toFixed(0)}%</span>
      </div>
      <p className="text-xs text-gray-500 mt-1">{signal.reasoning}</p>
      {signal.recommendedAction && (
        <p className="text-xs text-green-700 font-medium mt-1">→ {signal.recommendedAction}</p>
      )}
    </div>
  )
}

export default function AnalysisPanel({ plan, selectedPlantId }: Props) {
  const result = selectedPlantId
    ? plan.plantResults.find(r => r.plantId === selectedPlantId)
    : plan.plantResults[0]

  if (!result) return (
    <div className="card h-full flex items-center justify-center text-gray-400 text-sm">
      เลือกต้นไม้เพื่อดูผลการวิเคราะห์
    </div>
  )

  return (
    <div className="card space-y-3">
      <div>
        <h3 className="font-semibold text-gray-800">{result.plantName}</h3>
        <p className="text-xs text-gray-500">วิเคราะห์เมื่อ {new Date(plan.analyzedAt).toLocaleString('th-TH')}</p>
      </div>
      <AgentCard icon={Droplets}   label="การรดน้ำ"    signal={result.watering} />
      <AgentCard icon={Bug}        label="ศัตรูพืช"    signal={result.pestDetection} />
      <AgentCard icon={Scissors}   label="การเก็บเกี่ยว" signal={result.harvestPrediction} />
      <AgentCard icon={HeartPulse} label="โรคพืช"      signal={result.diseaseMonitor} />
    </div>
  )
}
