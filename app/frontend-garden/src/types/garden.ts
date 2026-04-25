export interface GardenZone {
  id: string
  name: string
  description: string
  areaSqm: number
  soilType: string
  irrigationType: string
  plants: Plant[]
}

export interface Plant {
  id: string
  zoneId: string
  name: string
  species: string
  variety: string
  plantedDate: string
  growthStage: 'seedling' | 'juvenile' | 'mature' | 'bearing' | 'dormant'
  healthStatus: 'healthy' | 'stressed' | 'diseased' | 'critical'
  positionX: number
  positionY: number
}

export interface GardenSignal {
  signal: string
  confidence: number
  reasoning: string
  recommendedAction?: string
}

export interface PlantAnalysisResult {
  plantId: string
  plantName: string
  watering: GardenSignal
  pestDetection: GardenSignal
  harvestPrediction: GardenSignal
  diseaseMonitor: GardenSignal
}

export interface GardenActionPlan {
  runId: string
  analyzedAt: string
  plantResults: PlantAnalysisResult[]
  prioritizedTasks: GardenTask[]
  summary: string
}

export interface AnalysisRun {
  id: string
  runDate: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  resultJson?: string
}

export interface GardenTask {
  id: string
  plantId?: string
  plant?: Plant
  taskType: 'water' | 'fertilize' | 'prune' | 'spray' | 'harvest'
  priority: 'urgent' | 'high' | 'medium' | 'low'
  dueDate: string
  status: 'pending' | 'in_progress' | 'completed' | 'skipped'
  instructions: string
  assignedWorkerId?: string
  completedAt?: string
}

export interface GardenObservation {
  id: string
  plantId: string
  plant?: Plant
  observationDate: string
  observer: string
  obsType: 'pest' | 'disease' | 'growth' | 'harvest' | 'general'
  severity: 'low' | 'medium' | 'high'
  notes: string
}

export const HEALTH_COLORS: Record<Plant['healthStatus'], string> = {
  healthy:  '#22c55e',
  stressed: '#eab308',
  diseased: '#f97316',
  critical: '#ef4444',
}

export const TASK_TYPE_LABELS: Record<GardenTask['taskType'], string> = {
  water:     'รดน้ำ',
  fertilize: 'ใส่ปุ๋ย',
  prune:     'ตัดแต่งกิ่ง',
  spray:     'พ่นยา',
  harvest:   'เก็บเกี่ยว',
}
