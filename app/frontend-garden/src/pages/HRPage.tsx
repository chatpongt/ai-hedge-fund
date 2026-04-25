import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { UserCheck, Clock, CheckCircle } from 'lucide-react'
import { hrApi } from '@/services/api'
import { Worker, WorkAssignment, AttendanceLog, PayrollSummary, ROLE_LABELS } from '@/types/hr'

function WorkerCard({ worker }: { worker: Worker }) {
  const statusColors: Record<Worker['status'], string> = {
    active: 'bg-green-100 text-green-700',
    on_leave: 'bg-yellow-100 text-yellow-700',
    inactive: 'bg-gray-100 text-gray-500',
  }
  const statusLabels = { active: 'ทำงาน', on_leave: 'ลาหยุด', inactive: 'ไม่ทำงาน' }
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-800">{worker.name}</h3>
          <p className="text-xs text-gray-500 mt-0.5">{ROLE_LABELS[worker.role]}</p>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[worker.status]}`}>{statusLabels[worker.status]}</span>
      </div>
      <div className="mt-3 flex items-center justify-between text-sm">
        <span className="text-gray-500">ค่าแรง/วัน</span>
        <span className="font-medium text-gray-800">฿{worker.dailyWage.toLocaleString()}</span>
      </div>
      <p className="text-xs text-gray-400 mt-1">{worker.contact}</p>
    </div>
  )
}

export default function HRPage() {
  const [workers, setWorkers] = useState<Worker[]>([])
  const [assignments, setAssignments] = useState<WorkAssignment[]>([])
  const [attendance, setAttendance] = useState<AttendanceLog[]>([])
  const [payroll, setPayroll] = useState<PayrollSummary[]>([])
  const [tab, setTab] = useState<'workers' | 'assignments' | 'attendance' | 'payroll'>('workers')

  useEffect(() => {
    const today = new Date()
    const load = async () => {
      try {
        const [w, a, att] = await Promise.all([
          hrApi.getWorkers(), hrApi.getAssignments(), hrApi.getAttendance({ year: today.getFullYear(), month: today.getMonth() + 1 }),
        ])
        setWorkers(w.data)
        setAssignments(a.data)
        setAttendance(att.data)

        const start = new Date(today.getFullYear(), today.getMonth(), 1)
        const end = new Date(today.getFullYear(), today.getMonth() + 1, 0)
        const pFormat = (d: Date) => d.toISOString().split('T')[0]
        const p = await hrApi.getPayroll({ periodStart: pFormat(start), periodEnd: pFormat(end) })
        setPayroll(p.data)
      } catch { toast.error('ไม่สามารถโหลดข้อมูลพนักงานได้') }
    }
    load()
  }, [])

  const completeAssignment = async (id: string) => {
    try {
      await hrApi.completeAssignment(id, { actualHours: 8 })
      setAssignments(prev => prev.map(a => a.id === id ? { ...a, status: 'completed' } : a))
      toast.success('บันทึกงานเสร็จแล้ว')
    } catch { toast.error('เกิดข้อผิดพลาด') }
  }

  const tabs = [
    { id: 'workers' as const, label: `พนักงาน (${workers.length})` },
    { id: 'assignments' as const, label: `งานที่มอบหมาย (${assignments.filter(a => a.status !== 'completed').length})` },
    { id: 'attendance' as const, label: 'บันทึกเวลา' },
    { id: 'payroll' as const, label: 'เงินเดือน' },
  ]

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">การบริหารทรัพยากรบุคคล</h1>
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <UserCheck className="w-4 h-4" />
          <span>พนักงานทำงานวันนี้: {attendance.filter(a => a.hoursWorked > 0 && a.date === new Date().toISOString().split('T')[0]).length}/{workers.length} คน</span>
        </div>
      </div>

      <div className="flex gap-4 border-b">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`text-sm font-medium pb-2 border-b-2 -mb-px ${tab === t.id ? 'border-green-600 text-green-700' : 'border-transparent text-gray-500'}`}>{t.label}</button>
        ))}
      </div>

      {tab === 'workers' && (
        <div className="grid grid-cols-3 gap-4">
          {workers.map(w => <WorkerCard key={w.id} worker={w} />)}
        </div>
      )}

      {tab === 'assignments' && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-gray-500 border-b">
              <th className="py-2 pr-4">พนักงาน</th><th className="py-2 pr-4">สถานะ</th>
              <th className="py-2 pr-4">ครบกำหนด</th><th className="py-2">การดำเนินการ</th>
            </tr></thead>
            <tbody>{assignments.map(a => (
              <tr key={a.id} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="py-2 pr-4 font-medium text-gray-800">{a.worker?.name ?? '-'}</td>
                <td className="py-2 pr-4">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${a.status === 'completed' ? 'bg-green-100 text-green-700' : a.status === 'in_progress' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}>
                    {a.status === 'completed' ? 'เสร็จแล้ว' : a.status === 'in_progress' ? 'กำลังทำ' : 'รอทำ'}
                  </span>
                </td>
                <td className="py-2 pr-4 text-gray-500">{new Date(a.dueDate).toLocaleDateString('th-TH')}</td>
                <td className="py-2">{a.status !== 'completed' && (
                  <button onClick={() => completeAssignment(a.id)} className="text-xs text-green-600 hover:text-green-700 flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" /> เสร็จแล้ว
                  </button>
                )}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}

      {tab === 'attendance' && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-gray-500 border-b">
              <th className="py-2 pr-4">พนักงาน</th><th className="py-2 pr-4">วันที่</th>
              <th className="py-2 pr-4">เข้างาน</th><th className="py-2 pr-4">ออกงาน</th>
              <th className="py-2 text-right">ชั่วโมง</th>
            </tr></thead>
            <tbody>{attendance.slice(0, 30).map(a => (
              <tr key={a.id} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="py-2 pr-4 font-medium">{a.worker?.name ?? '-'}</td>
                <td className="py-2 pr-4 text-gray-500">{new Date(a.date).toLocaleDateString('th-TH')}</td>
                <td className="py-2 pr-4">{a.clockIn ?? <span className="text-red-400">ขาด</span>}</td>
                <td className="py-2 pr-4">{a.clockOut ?? '-'}</td>
                <td className="py-2 text-right"><span className="flex items-center justify-end gap-1"><Clock className="w-3 h-3 text-gray-400" />{a.hoursWorked}</span></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}

      {tab === 'payroll' && (
        <div className="space-y-3">
          <h2 className="font-semibold text-gray-700">สรุปเงินเดือนประจำเดือนนี้</h2>
          <div className="grid grid-cols-3 gap-4">
            {payroll.map(p => (
              <div key={p.workerId} className="card">
                <h3 className="font-medium text-gray-800">{p.workerName}</h3>
                <div className="mt-2 space-y-1 text-sm">
                  <div className="flex justify-between text-gray-500"><span>วันที่ทำงาน</span><span>{p.daysWorked} วัน</span></div>
                  <div className="flex justify-between font-semibold text-gray-800"><span>รวม</span><span>฿{p.totalAmount.toLocaleString()}</span></div>
                </div>
              </div>
            ))}
          </div>
          <div className="card bg-green-50 border border-green-200">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-green-800">รวมค่าแรงทั้งหมด</span>
              <span className="text-xl font-bold text-green-700">฿{payroll.reduce((s, p) => s + p.totalAmount, 0).toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
