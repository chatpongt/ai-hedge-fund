import { useState, useEffect, useCallback } from 'react'
import { toast } from 'sonner'
import { Play, RefreshCw } from 'lucide-react'
import { gardenApi } from '@/services/api'
import { Plant, GardenZone, GardenTask, GardenActionPlan, AnalysisRun } from '@/types/garden'
import GardenMap from '@/components/garden/GardenMap'
import AnalysisPanel from '@/components/garden/AnalysisPanel'
import TaskList from '@/components/garden/TaskList'
import PlantHealthCard from '@/components/garden/PlantHealthCard'

export default function GardenPage() {
  const [zones, setZones] = useState<GardenZone[]>([])
  const [plants, setPlants] = useState<Plant[]>([])
  const [tasks, setTasks] = useState<GardenTask[]>([])
  const [selectedPlantId, setSelectedPlantId] = useState<string>()
  const [actionPlan, setActionPlan] = useState<GardenActionPlan | null>(null)
  const [analyzing, setAnalyzing] = useState(false)

  const loadData = useCallback(async () => {
    try {
      const [z, p, t] = await Promise.all([gardenApi.getZones(), gardenApi.getPlants(), gardenApi.getTasks({ status: 'pending' })])
      setZones(z.data)
      setPlants(p.data)
      setTasks(t.data)
    } catch {
      toast.error('ไม่สามารถโหลดข้อมูลได้')
    }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  const runAnalysis = async () => {
    setAnalyzing(true)
    try {
      const { data: run }: { data: AnalysisRun } = await gardenApi.runAnalysis()
      toast.info('กำลังวิเคราะห์สวน...')
      // Poll for result
      const poll = async () => {
        const { data: updated }: { data: AnalysisRun } = await gardenApi.getAnalysis(run.id)
        if (updated.status === 'completed' && updated.resultJson) {
          const plan: GardenActionPlan = JSON.parse(updated.resultJson)
          setActionPlan(plan)
          setTasks(prev => [...plan.prioritizedTasks.map(t => ({ ...t, id: t.id || crypto.randomUUID() })), ...prev])
          setAnalyzing(false)
          toast.success(plan.summary)
        } else if (updated.status === 'failed') {
          setAnalyzing(false)
          toast.error('การวิเคราะห์ล้มเหลว')
        } else {
          setTimeout(poll, 1500)
        }
      }
      setTimeout(poll, 1000)
    } catch {
      setAnalyzing(false)
      toast.error('ไม่สามารถเริ่มการวิเคราะห์ได้')
    }
  }

  const completeTask = async (id: string) => {
    try {
      await gardenApi.completeTask(id)
      setTasks(prev => prev.filter(t => t.id !== id))
      toast.success('ทำเครื่องหมายงานเสร็จแล้ว')
    } catch {
      toast.error('เกิดข้อผิดพลาด')
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-800">สวนผลไม้ของฉัน</h1>
          <p className="text-sm text-gray-500">{plants.length} ต้น · {zones.length} โซน</p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadData} className="btn-secondary flex items-center gap-2">
            <RefreshCw className="w-4 h-4" /> รีเฟรช
          </button>
          <button onClick={runAnalysis} disabled={analyzing} className="btn-primary flex items-center gap-2">
            <Play className="w-4 h-4" />
            {analyzing ? 'กำลังวิเคราะห์...' : 'วิเคราะห์สวน'}
          </button>
        </div>
      </div>

      {/* Main area */}
      <div className="flex-1 overflow-hidden p-4 grid grid-cols-3 gap-4">
        {/* Garden Map */}
        <div className="col-span-2 flex flex-col gap-4">
          <div className="flex-1 min-h-0">
            <GardenMap zones={zones} plants={plants} selectedPlantId={selectedPlantId} onSelectPlant={setSelectedPlantId} />
          </div>
          {/* Plant cards */}
          <div className="grid grid-cols-4 gap-2">
            {plants.map(p => (
              <PlantHealthCard key={p.id} plant={p} selected={selectedPlantId === p.id} onClick={() => setSelectedPlantId(p.id)} />
            ))}
          </div>
        </div>

        {/* Right panel: Analysis + Tasks */}
        <div className="flex flex-col gap-4 overflow-hidden">
          {actionPlan
            ? <AnalysisPanel plan={actionPlan} selectedPlantId={selectedPlantId} />
            : <div className="card flex items-center justify-center text-gray-400 text-sm h-64">
                กดปุ่ม "วิเคราะห์สวน" เพื่อเริ่มต้น
              </div>
          }
          <div className="flex-1 overflow-hidden">
            <TaskList tasks={tasks} onComplete={completeTask} />
          </div>
        </div>
      </div>
    </div>
  )
}
