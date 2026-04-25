import { GardenTask, TASK_TYPE_LABELS } from '@/types/garden'
import { CheckCircle, Clock } from 'lucide-react'

interface Props {
  tasks: GardenTask[]
  onComplete: (id: string) => void
}

const PRIORITY_ORDER = ['urgent', 'high', 'medium', 'low']
const PRIORITY_LABELS: Record<string, string> = {
  urgent: 'เร่งด่วน', high: 'สูง', medium: 'ปานกลาง', low: 'ต่ำ',
}

export default function TaskList({ tasks, onComplete }: Props) {
  const pending = tasks.filter(t => t.status !== 'completed')
  const grouped = PRIORITY_ORDER.reduce<Record<string, GardenTask[]>>((acc, p) => {
    const items = pending.filter(t => t.priority === p)
    if (items.length) acc[p] = items
    return acc
  }, {})

  return (
    <div className="card space-y-4 overflow-y-auto max-h-full">
      <h3 className="font-semibold text-gray-800">งานที่ต้องทำ ({pending.length})</h3>
      {Object.entries(grouped).map(([priority, items]) => (
        <div key={priority}>
          <p className="text-xs font-medium text-gray-500 uppercase mb-2">{PRIORITY_LABELS[priority]}</p>
          <div className="space-y-2">
            {items.map(task => (
              <div key={task.id} className="flex items-start gap-2 p-2 rounded-lg bg-gray-50 hover:bg-gray-100 group">
                <button onClick={() => onComplete(task.id)} className="mt-0.5 text-gray-300 hover:text-green-500 transition-colors">
                  <CheckCircle className="w-4 h-4" />
                </button>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className={`badge-${priority}`}>{TASK_TYPE_LABELS[task.taskType]}</span>
                    {task.plant && <span className="text-xs text-gray-500 truncate">{task.plant.name}</span>}
                  </div>
                  <p className="text-xs text-gray-600 mt-0.5">{task.instructions}</p>
                  <div className="flex items-center gap-1 mt-1 text-xs text-gray-400">
                    <Clock className="w-3 h-3" />
                    <span>ครบกำหนด {new Date(task.dueDate).toLocaleDateString('th-TH')}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      {pending.length === 0 && (
        <p className="text-sm text-gray-400 text-center py-4">ไม่มีงานที่ค้างอยู่</p>
      )}
    </div>
  )
}
