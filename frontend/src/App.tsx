import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/AppShell'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { useAuth } from '@/context/AuthContext'
import {
  AdminAuditPage,
  AdminDoctorsPage,
  AdminPatientsPage,
  AdminSpecializationsPage,
} from '@/pages/AdminPages'
import { AppointmentsPage } from '@/pages/AppointmentsPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { DoctorDetailPage } from '@/pages/DoctorDetailPage'
import { DoctorsPage } from '@/pages/DoctorsPage'
import { LandingPage } from '@/pages/LandingPage'
import { LoginPage } from '@/pages/LoginPage'
import { NotificationsPage } from '@/pages/NotificationsPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { RecordsPage } from '@/pages/RecordsPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { SchedulePage } from '@/pages/SchedulePage'

function HomeRedirect() {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <LandingPage />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/appointments" element={<AppointmentsPage />} />

          <Route element={<ProtectedRoute roles={['patient']} />}>
            <Route path="/doctors" element={<DoctorsPage />} />
            <Route path="/doctors/:doctorId" element={<DoctorDetailPage />} />
            <Route path="/records" element={<RecordsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>

          <Route element={<ProtectedRoute roles={['doctor']} />}>
            <Route path="/schedule" element={<SchedulePage />} />
          </Route>

          <Route element={<ProtectedRoute roles={['admin']} />}>
            <Route path="/admin/patients" element={<AdminPatientsPage />} />
            <Route path="/admin/doctors" element={<AdminDoctorsPage />} />
            <Route path="/admin/specializations" element={<AdminSpecializationsPage />} />
            <Route path="/admin/audit" element={<AdminAuditPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
