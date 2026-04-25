export interface Equipment {
  id: string
  name: string
  equipmentType: 'tractor' | 'sprayer' | 'irrigation_pump' | 'hand_tool' | 'vehicle'
  brand: string
  model: string
  purchaseDate: string
  purchaseCost: number
  status: 'operational' | 'maintenance' | 'repair' | 'retired'
  totalHoursUsed: number
  nextMaintenanceHours: number
  nextMaintenanceDate?: string
}

export interface UsageLog {
  id: string
  equipmentId: string
  workerId?: string
  usageDate: string
  hoursUsed: number
  taskDescription: string
}

export interface MaintenanceRecord {
  id: string
  equipmentId: string
  maintenanceDate: string
  maintenanceType: 'oil_change' | 'filter' | 'belt' | 'inspection' | 'calibration'
  cost: number
  doneBy: string
  notes: string
  nextDueDate?: string
}

export interface RepairRecord {
  id: string
  equipmentId: string
  reportedDate: string
  repairedDate?: string
  issueDescription: string
  repairCost: number
  repairedBy: string
  status: 'pending' | 'in_repair' | 'completed'
}

export const EQUIPMENT_TYPE_LABELS: Record<Equipment['equipmentType'], string> = {
  tractor:          'รถไถ',
  sprayer:          'เครื่องพ่นยา',
  irrigation_pump:  'ปั๊มน้ำ',
  hand_tool:        'เครื่องมือมือ',
  vehicle:          'ยานพาหนะ',
}

export const STATUS_COLORS: Record<Equipment['status'], string> = {
  operational: 'bg-green-100 text-green-700',
  maintenance: 'bg-yellow-100 text-yellow-700',
  repair:      'bg-red-100 text-red-700',
  retired:     'bg-gray-100 text-gray-500',
}
