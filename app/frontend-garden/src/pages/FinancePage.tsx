import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { TrendingUp, TrendingDown, DollarSign, BarChart3, Plus } from 'lucide-react'
import { financeApi } from '@/services/api'
import { FinanceSummary, MonthlyReport, IncomeRecord, ExpenseRecord, EXPENSE_CATEGORY_LABELS } from '@/types/finance'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'

function SummaryCard({ label, value, icon: Icon, color }: { label: string; value: string; icon: React.ElementType; color: string }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-xl ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-xl font-bold text-gray-800">{value}</p>
      </div>
    </div>
  )
}

function formatBaht(n: number) {
  return `฿${n.toLocaleString('th-TH', { minimumFractionDigits: 0 })}`
}

export default function FinancePage() {
  const [summary, setSummary] = useState<FinanceSummary | null>(null)
  const [monthly, setMonthly] = useState<MonthlyReport[]>([])
  const [income, setIncome] = useState<IncomeRecord[]>([])
  const [expenses, setExpenses] = useState<ExpenseRecord[]>([])
  const [tab, setTab] = useState<'income' | 'expense'>('income')

  useEffect(() => {
    const load = async () => {
      try {
        const [s, m, i, e] = await Promise.all([
          financeApi.getSummary(), financeApi.getMonthly(), financeApi.getIncome(), financeApi.getExpenses(),
        ])
        setSummary(s.data)
        setMonthly(m.data.map((r: MonthlyReport) => ({ ...r, month: r.month.slice(5) })))
        setIncome(i.data)
        setExpenses(e.data)
      } catch { toast.error('ไม่สามารถโหลดข้อมูลการเงินได้') }
    }
    load()
  }, [])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">การบริหารการเงิน</h1>
        <div className="flex gap-2">
          <button className="btn-secondary flex items-center gap-2 text-sm"><Plus className="w-4 h-4" />รายรับ</button>
          <button className="btn-primary flex items-center gap-2 text-sm"><Plus className="w-4 h-4" />รายจ่าย</button>
        </div>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-4 gap-4">
          <SummaryCard label="รายรับทั้งหมด" value={formatBaht(summary.totalIncome)} icon={TrendingUp} color="bg-green-100 text-green-600" />
          <SummaryCard label="รายจ่ายทั้งหมด" value={formatBaht(summary.totalExpense)} icon={TrendingDown} color="bg-red-100 text-red-600" />
          <SummaryCard label="กำไรสุทธิ" value={formatBaht(summary.netProfit)} icon={DollarSign} color={summary.netProfit >= 0 ? 'bg-blue-100 text-blue-600' : 'bg-orange-100 text-orange-600'} />
          <SummaryCard label="ROI" value={`${summary.roi.toFixed(1)}%`} icon={BarChart3} color="bg-purple-100 text-purple-600" />
        </div>
      )}

      {/* Monthly chart */}
      <div className="card">
        <h2 className="font-semibold text-gray-700 mb-4">รายได้-รายจ่าย รายเดือน</h2>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={monthly}>
            <XAxis dataKey="month" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
            <Tooltip formatter={(v: number) => formatBaht(v)} />
            <Legend />
            <Bar dataKey="income" name="รายรับ" fill="#22c55e" radius={[4, 4, 0, 0]} />
            <Bar dataKey="expense" name="รายจ่าย" fill="#f87171" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Transactions */}
      <div className="card">
        <div className="flex gap-4 mb-4">
          <button onClick={() => setTab('income')} className={`text-sm font-medium pb-1 border-b-2 ${tab === 'income' ? 'border-green-600 text-green-700' : 'border-transparent text-gray-500'}`}>รายรับ ({income.length})</button>
          <button onClick={() => setTab('expense')} className={`text-sm font-medium pb-1 border-b-2 ${tab === 'expense' ? 'border-green-600 text-green-700' : 'border-transparent text-gray-500'}`}>รายจ่าย ({expenses.length})</button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-gray-500 border-b">{
              tab === 'income'
                ? <><th className="py-2 pr-4">วันที่</th><th className="py-2 pr-4">ประเภท</th><th className="py-2 pr-4">หมายเหตุ</th><th className="py-2 text-right">จำนวน</th></>
                : <><th className="py-2 pr-4">วันที่</th><th className="py-2 pr-4">หมวดหมู่</th><th className="py-2 pr-4">รายละเอียด</th><th className="py-2 text-right">จำนวน</th></>
            }</tr></thead>
            <tbody>{
              tab === 'income'
                ? income.slice(0, 20).map(r => (
                    <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 pr-4 text-gray-500">{new Date(r.date).toLocaleDateString('th-TH')}</td>
                      <td className="py-2 pr-4 text-gray-600">{r.source}</td>
                      <td className="py-2 pr-4 text-gray-600 truncate max-w-xs">{r.notes}</td>
                      <td className="py-2 text-right text-green-600 font-medium">{formatBaht(r.amount)}</td>
                    </tr>
                  ))
                : expenses.slice(0, 20).map(r => (
                    <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 pr-4 text-gray-500">{new Date(r.date).toLocaleDateString('th-TH')}</td>
                      <td className="py-2 pr-4"><span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs">{EXPENSE_CATEGORY_LABELS[r.category]}</span></td>
                      <td className="py-2 pr-4 text-gray-600 truncate max-w-xs">{r.description}</td>
                      <td className="py-2 text-right text-red-600 font-medium">{formatBaht(r.amount)}</td>
                    </tr>
                  ))
            }</tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
