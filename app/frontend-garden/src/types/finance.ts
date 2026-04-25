export interface IncomeRecord {
  id: string
  plantId?: string
  date: string
  amount: number
  source: 'harvest_sale' | 'subsidy' | 'other'
  quantityKg?: number
  pricePerKg?: number
  notes: string
}

export interface ExpenseRecord {
  id: string
  plantId?: string
  date: string
  amount: number
  category: 'fertilizer' | 'pesticide' | 'labor' | 'water' | 'equipment' | 'other'
  description: string
  vendor?: string
}

export interface FinanceSummary {
  totalIncome: number
  totalExpense: number
  netProfit: number
  roi: number
}

export interface MonthlyReport {
  month: string
  income: number
  expense: number
  profit: number
}

export const EXPENSE_CATEGORY_LABELS: Record<ExpenseRecord['category'], string> = {
  fertilizer: 'ปุ๋ย',
  pesticide:  'ยาฆ่าแมลง',
  labor:      'แรงงาน',
  water:      'น้ำ',
  equipment:  'อุปกรณ์',
  other:      'อื่นๆ',
}
