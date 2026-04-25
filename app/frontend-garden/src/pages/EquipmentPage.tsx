import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { AlertTriangle, Wrench, Clock, CheckCircle } from 'lucide-react'
import { equipmentApi } from '@/services/api'
import { Equipment, MaintenanceRecord, RepairRecord, EQUIPMENT_TYPE_LABELS, STATUS_COLORS } from '@/types/equipment'

function EquipmentCard({ equip, isDue, onClick, selected }: { equip: Equipment; isDue: boolean; onClick: () => void; selected: boolean }) {
  const pct = Math.min(100, (equip.totalHoursUsed / equip.nextMaintenanceHours) * 100)
  return (
    <div onClick={onClick} className={`card cursor-pointer transition-all ${selected ? 'ring-2 ring-green-500' : 'hover:shadow-md'} ${isDue ? 'border-orange-200' : ''}`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-1.5">
            {isDue && <AlertTriangle className="w-3.5 h-3.5 text-orange-500" />}
            <h3 className="font-semibold text-gray-800 text-sm">{equip.name}</h3>
          </div>
          <p className="text-xs text-gray-500">{EQUIPMENT_TYPE_LABELS[equip.equipmentType]} · {equip.brand}</p>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[equip.status]}`}>
          {{ operational: 'ใช้งานได้', maintenance: 'บำรุงรักษา', repair: 'ซ่อม', retired: 'เลิกใช้' }[equip.status]}
        </span>
      </div>
      <div className="mt-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>ชั่วโมงใช้งาน</span>
          <span>{equip.totalHoursUsed.toFixed(0)} / {equip.nextMaintenanceHours} ชม.</span>
        </div>
        <div className="bg-gray-100 rounded-full h-1.5">
          <div className={`h-1.5 rounded-full ${pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-orange-400' : 'bg-green-500'}`} style={{ width: `${pct}%` }} />
        </div>
      </div>
      {equip.nextMaintenanceDate && (
        <p className="mt-2 text-xs text-gray-400 flex items-center gap-1">
          <Clock className="w-3 h-3" /> บำรุงรักษาถัดไป: {new Date(equip.nextMaintenanceDate).toLocaleDateString('th-TH')}
        </p>
      )}
    </div>
  )
}

export default function EquipmentPage() {
  const [equipment, setEquipment] = useState<Equipment[]>([])
  const [dueEquipment, setDueEquipment] = useState<Equipment[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [maintenance, setMaintenance] = useState<MaintenanceRecord[]>([])
  const [repairs, setRepairs] = useState<RepairRecord[]>([])
  const [costSummary, setCostSummary] = useState<{ maintenanceCost: number; repairCost: number; totalCost: number } | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [e, due, cost] = await Promise.all([equipmentApi.getAll(), equipmentApi.getMaintenanceDue(), equipmentApi.getCostSummary()])
        setEquipment(e.data)
        setDueEquipment(due.data)
        setCostSummary(cost.data)
      } catch { toast.error('ไม่สามารถโหลดข้อมูลอุปกรณ์ได้') }
    }
    load()
  }, [])

  const loadDetail = async (id: string) => {
    setSelectedId(id)
    try {
      const [m, r] = await Promise.all([equipmentApi.getMaintenanceHist(id), equipmentApi.getRepairHist(id)])
      setMaintenance(m.data)
      setRepairs(r.data)
    } catch { toast.error('ไม่สามารถโหลดประวัติได้') }
  }

  const dueIds = new Set(dueEquipment.map(e => e.id))
  const selected = selectedId ? equipment.find(e => e.id === selectedId) : null

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">การบริหารเครื่องจักรและอุปกรณ์</h1>
        {costSummary && (
          <div className="flex gap-4 text-sm text-gray-500">
            <span>บำรุงรักษา: <strong className="text-gray-700">฿{costSummary.maintenanceCost.toLocaleString()}</strong></span>
            <span>ซ่อม: <strong className="text-gray-700">฿{costSummary.repairCost.toLocaleString()}</strong></span>
          </div>
        )}
      </div>

      {dueEquipment.length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
          <div className="flex items-center gap-2 text-orange-700 font-medium mb-2">
            <AlertTriangle className="w-4 h-4" /> แจ้งเตือนบำรุงรักษา ({dueEquipment.length} รายการ)
          </div>
          <div className="flex flex-wrap gap-2">
            {dueEquipment.map(e => (
              <span key={e.id} className="bg-orange-100 text-orange-700 text-xs px-2 py-1 rounded-full flex items-center gap-1">
                <Wrench className="w-3 h-3" />{e.name}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        {equipment.map(e => (
          <EquipmentCard key={e.id} equip={e} isDue={dueIds.has(e.id)} onClick={() => loadDetail(e.id)} selected={selectedId === e.id} />
        ))}
      </div>

      {selected && (
        <div className="grid grid-cols-2 gap-4">
          <div className="card">
            <h3 className="font-semibold text-gray-700 mb-3">ประวัติการบำรุงรักษา — {selected.name}</h3>
            {maintenance.length === 0 ? <p className="text-sm text-gray-400">ยังไม่มีประวัติ</p> : (
              <div className="space-y-2">
                {maintenance.map(m => (
                  <div key={m.id} className="flex items-start gap-2 p-2 bg-green-50 rounded-lg">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                    <div className="text-sm">
                      <p className="font-medium text-gray-700">{m.maintenanceType.replace(/_/g, ' ')}</p>
                      <p className="text-xs text-gray-500">{new Date(m.maintenanceDate).toLocaleDateString('th-TH')} · ฿{m.cost.toLocaleString()} · {m.doneBy}</p>
                      {m.notes && <p className="text-xs text-gray-400">{m.notes}</p>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="card">
            <h3 className="font-semibold text-gray-700 mb-3">ประวัติการซ่อม — {selected.name}</h3>
            {repairs.length === 0 ? <p className="text-sm text-gray-400">ยังไม่มีประวัติ</p> : (
              <div className="space-y-2">
                {repairs.map(r => (
                  <div key={r.id} className={`flex items-start gap-2 p-2 rounded-lg ${r.status === 'completed' ? 'bg-gray-50' : 'bg-red-50'}`}>
                    <AlertTriangle className={`w-4 h-4 mt-0.5 shrink-0 ${r.status === 'completed' ? 'text-gray-400' : 'text-red-400'}`} />
                    <div className="text-sm">
                      <p className="font-medium text-gray-700">{r.issueDescription}</p>
                      <p className="text-xs text-gray-500">
                        แจ้ง {new Date(r.reportedDate).toLocaleDateString('th-TH')}
                        {r.repairedDate && ` · ซ่อมเสร็จ ${new Date(r.repairedDate).toLocaleDateString('th-TH')}`}
                        {r.repairCost > 0 && ` · ฿${r.repairCost.toLocaleString()}`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
