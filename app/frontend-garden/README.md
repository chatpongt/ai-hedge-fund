# Fruit Garden Management — Frontend

React + TypeScript + Tailwind CSS frontend สำหรับระบบบริหารจัดการสวนผลไม้

## Quick Start

```bash
cd app/frontend-garden
npm install
npm run dev
```

Frontend starts at `http://localhost:5174`  
Backend must be running at `http://localhost:5000`

## Pages

| Path | Description |
|------|-------------|
| `/garden` | แผนที่สวน, AI analysis, รายการงาน |
| `/finance` | รายรับ-รายจ่าย, กราฟ, ROI |
| `/hr` | พนักงาน, งานที่มอบหมาย, บันทึกเวลา, เงินเดือน |
| `/equipment` | อุปกรณ์, แจ้งเตือนบำรุงรักษา, ประวัติซ่อม |

## Stack
- React 18 + React Router 6
- TypeScript
- Tailwind CSS
- @xyflow/react (garden map visualization)
- Recharts (finance charts)
- Sonner (toast notifications)
- Axios (API calls)
