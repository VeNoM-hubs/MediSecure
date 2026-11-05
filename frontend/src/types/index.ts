export type Role = 'patient' | 'doctor' | 'admin'

export interface AuthUser {
  user_id: string
  full_name: string
  role: Role
  access_token: string
  refresh_token?: string
}

export interface UserPublic {
  id: string
  email: string
  full_name: string
  role: Role
  is_active: boolean
  phone?: string | null
}

export interface Doctor {
  id: string
  user_id: string
  email: string
  full_name: string
  specialization_name?: string | null
  qualifications?: string | null
  availability_notes?: string | null
  bio?: string | null
  years_experience: number
  is_active: boolean
}

export interface Appointment {
  id: string
  patient_id: string
  doctor_id: string
  scheduled_at: string
  status: string
  reason?: string | null
  consultation_notes?: string | null
  patient_name?: string | null
  doctor_name?: string | null
}

export interface MedicalRecord {
  id: string
  patient_id: string
  title: string
  diagnosis?: string | null
  treatment?: string | null
  notes?: string | null
  record_date: string
}

export interface NotificationItem {
  id: string
  title: string
  message: string
  is_read: boolean
  category: string
  created_at: string
}

export interface Stats {
  total_patients: number
  total_doctors: number
  total_appointments: number
  active_users: number
  recent_security_events: number
}

export interface AuditLog {
  id: string
  actor_email?: string | null
  actor_role?: string | null
  action: string
  detail?: string | null
  success: boolean
  created_at: string
}

export interface Specialization {
  id: string
  name: string
  description?: string | null
}

export interface PatientProfile {
  id: string
  user_id: string
  email: string
  full_name: string
  phone?: string | null
  is_active: boolean
  date_of_birth?: string | null
  gender?: string | null
  blood_type?: string | null
  address?: string | null
  emergency_contact?: string | null
}
