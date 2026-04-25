export interface Worker {
  id: string
  name: string
  role: 'general_worker' | 'specialist' | 'supervisor' | 'permanent' | 'seasonal'
  dailyWage: number
  startDate: string
  status: 'active' | 'on_leave' | 'inactive'
  contact: string
}

export interface WorkAssignment {
  id: string
  taskId: string
  workerId: string
  worker?: Worker
  assignedDate: string
  dueDate: string
  status: 'assigned' | 'in_progress' | 'completed'
  actualHours?: number
  completionNotes?: string
  completedAt?: string
}

export interface AttendanceLog {
  id: string
  workerId: string
  worker?: Worker
  date: string
  clockIn?: string
  clockOut?: string
  hoursWorked: number
  absenceReason?: string
}

export interface PayrollSummary {
  workerId: string
  workerName: string
  daysWorked: number
  totalAmount: number
}

export const ROLE_LABELS: Record<Worker['role'], string> = {
  general_worker: 'คนงานทั่วไป',
  specialist:     'ผู้เชี่ยวชาญ',
  supervisor:     'หัวหน้างาน',
  permanent:      'พนักงานประจำ',
  seasonal:       'แรงงานตามฤดูกาล',
}
