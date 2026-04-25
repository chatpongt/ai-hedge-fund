import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { Leaf, DollarSign, Users, Wrench } from 'lucide-react'
import { Toaster } from 'sonner'
import GardenPage from './pages/GardenPage'
import FinancePage from './pages/FinancePage'
import HRPage from './pages/HRPage'
import EquipmentPage from './pages/EquipmentPage'

const navItems = [
  { to: '/garden',    icon: Leaf,        label: 'สวน' },
  { to: '/finance',   icon: DollarSign,  label: 'การเงิน' },
  { to: '/hr',        icon: Users,       label: 'พนักงาน' },
  { to: '/equipment', icon: Wrench,      label: 'อุปกรณ์' },
]

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Toaster richColors position="top-right" />

      {/* Sidebar */}
      <aside className="w-56 bg-green-700 text-white flex flex-col shrink-0">
        <div className="p-4 border-b border-green-600">
          <div className="flex items-center gap-2">
            <Leaf className="w-6 h-6" />
            <span className="font-bold text-lg">สวนผลไม้</span>
          </div>
          <p className="text-green-200 text-xs mt-1">ระบบบริหารจัดการ</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? 'bg-green-600 text-white' : 'text-green-100 hover:bg-green-600/50'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-green-600 text-green-300 text-xs">
          v1.0 · Fruit Garden Mgmt
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<Navigate to="/garden" replace />} />
          <Route path="/garden" element={<GardenPage />} />
          <Route path="/finance" element={<FinancePage />} />
          <Route path="/hr" element={<HRPage />} />
          <Route path="/equipment" element={<EquipmentPage />} />
        </Routes>
      </main>
    </div>
  )
}
