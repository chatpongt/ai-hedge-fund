import axios from 'axios'

const api = axios.create({ baseURL: '/api', headers: { 'Content-Type': 'application/json' } })

export default api

// Garden
export const gardenApi = {
  getZones:          () => api.get('/garden/zones'),
  createZone:        (data: object) => api.post('/garden/zones', data),
  getPlants:         (zoneId?: string) => api.get('/garden/plants', { params: { zoneId } }),
  getPlant:          (id: string) => api.get(`/garden/plants/${id}`),
  createPlant:       (data: object) => api.post('/garden/plants', data),
  updatePlant:       (id: string, data: object) => api.put(`/garden/plants/${id}`, data),
  getTasks:          (params?: object) => api.get('/garden/tasks', { params }),
  createTask:        (data: object) => api.post('/garden/tasks', data),
  completeTask:      (id: string) => api.put(`/garden/tasks/${id}/complete`),
  getObservations:   (plantId?: string) => api.get('/garden/observations', { params: { plantId } }),
  createObservation: (data: object) => api.post('/garden/observations', data),
  runAnalysis:       (plantIds?: string[]) => api.post('/analysis/run', plantIds),
  getAnalysis:       (runId: string) => api.get(`/analysis/${runId}`),
  seedMock:          () => api.post('/mock/seed'),
}

// Finance
export const financeApi = {
  getSummary:    (params?: object) => api.get('/finance/summary', { params }),
  getIncome:     (params?: object) => api.get('/finance/income', { params }),
  createIncome:  (data: object) => api.post('/finance/income', data),
  getExpenses:   (params?: object) => api.get('/finance/expenses', { params }),
  createExpense: (data: object) => api.post('/finance/expenses', data),
  getMonthly:    (months = 6) => api.get('/finance/reports/monthly', { params: { months } }),
  getBudget:     (period: string) => api.get('/finance/budget', { params: { period } }),
  upsertBudget:  (data: object) => api.put('/finance/budget', data),
}

// HR
export const hrApi = {
  getWorkers:          () => api.get('/hr/workers'),
  createWorker:        (data: object) => api.post('/hr/workers', data),
  updateWorker:        (id: string, data: object) => api.put(`/hr/workers/${id}`, data),
  getAssignments:      (params?: object) => api.get('/hr/assignments', { params }),
  createAssignment:    (data: object) => api.post('/hr/assignments', data),
  completeAssignment:  (id: string, params?: object) => api.put(`/hr/assignments/${id}/complete`, null, { params }),
  logAttendance:       (data: object) => api.post('/hr/attendance', data),
  getAttendance:       (params?: object) => api.get('/hr/attendance', { params }),
  getPayroll:          (params: object) => api.get('/hr/payroll', { params }),
  recordPayroll:       (data: object) => api.post('/hr/payroll/record', data),
}

// Equipment
export const equipmentApi = {
  getAll:              () => api.get('/equipment'),
  create:              (data: object) => api.post('/equipment', data),
  getById:             (id: string) => api.get(`/equipment/${id}`),
  update:              (id: string, data: object) => api.put(`/equipment/${id}`, data),
  logUsage:            (id: string, data: object) => api.post(`/equipment/${id}/usage`, data),
  getMaintenanceDue:   () => api.get('/equipment/maintenance/due'),
  recordMaintenance:   (id: string, data: object) => api.post(`/equipment/${id}/maintenance`, data),
  getMaintenanceHist:  (id: string) => api.get(`/equipment/${id}/maintenance`),
  recordRepair:        (id: string, data: object) => api.post(`/equipment/${id}/repair`, data),
  getRepairHist:       (id: string) => api.get(`/equipment/${id}/repair`),
  getCostSummary:      (params?: object) => api.get('/equipment/costs/summary', { params }),
}
