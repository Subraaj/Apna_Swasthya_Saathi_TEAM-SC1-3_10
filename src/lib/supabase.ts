import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://your-project.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'your-anon-key'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Database types
export interface User {
  id: string
  email: string
  user_type: 'asha' | 'citizen' | 'admin'
  full_name: string
  phone?: string
  abha_id?: string
  district?: string
  block?: string
  village?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AshaWorker {
  id: string
  user_id: string
  asha_id: string
  certification_number?: string
  assigned_villages: string[]
  supervisor_contact?: string
  training_status: string
  performance_score: number
  created_at: string
}

export interface Citizen {
  id: string
  user_id: string
  date_of_birth?: string
  gender?: string
  blood_group?: string
  emergency_contact?: string
  medical_history?: any
  insurance_details?: any
  created_at: string
}

export interface HealthRecord {
  id: string
  citizen_id: string
  asha_id?: string
  record_type: string
  diagnosis?: any
  symptoms?: any
  vital_signs?: any
  medications?: any
  lab_results?: any
  recommendations?: string
  risk_level?: string
  follow_up_date?: string
  created_at: string
}

export interface EmergencyAlert {
  id: string
  citizen_id: string
  alert_type: string
  severity: string
  location?: any
  description?: string
  status: string
  responder_id?: string
  response_time?: string
  resolution_time?: string
  created_at: string
}

export interface InsurancePolicy {
  id: string
  citizen_id: string
  policy_type: string
  policy_number: string
  premium_amount: number
  coverage_amount: number
  start_date: string
  end_date: string
  status: string
  claims?: any
  created_at: string
}

export interface ChatSession {
  id: string
  user_id: string
  session_data: any
  language: string
  created_at: string
  updated_at?: string
}

export interface HealthcareFacility {
  id: string
  name: string
  type: string
  address: string
  district: string
  block?: string
  coordinates?: any
  contact_info?: any
  services?: any
  bsky_empanelled: boolean
  operating_hours?: any
  rating?: number
  created_at: string
}