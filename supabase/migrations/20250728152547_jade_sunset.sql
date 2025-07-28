/*
  # Initial Schema for Apna Swasthya Saathi

  1. New Tables
    - `users` - User accounts (ASHA workers, citizens, admins)
    - `asha_workers` - ASHA worker profiles
    - `citizens` - Citizen profiles  
    - `health_records` - Health records and diagnoses
    - `ai_diagnoses` - AI analysis results
    - `government_schemes` - Government scheme applications
    - `insurance_policies` - Insurance policies and claims
    - `emergency_alerts` - Emergency alerts and responses
    - `healthcare_facilities` - Healthcare facility directory
    - `chat_sessions` - Chat conversation history

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users
    - Secure data access based on user roles

  3. Indexes
    - Performance optimization indexes
    - Search and query optimization
*/

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  user_type VARCHAR(50) NOT NULL CHECK (user_type IN ('asha', 'citizen', 'admin')),
  full_name VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  abha_id VARCHAR(50) UNIQUE,
  district VARCHAR(100),
  block VARCHAR(100),
  village VARCHAR(100),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ASHA Workers table
CREATE TABLE IF NOT EXISTS asha_workers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  asha_id VARCHAR(50) UNIQUE NOT NULL,
  certification_number VARCHAR(100),
  assigned_villages TEXT[],
  supervisor_contact VARCHAR(20),
  training_status VARCHAR(50) DEFAULT 'pending',
  performance_score DECIMAL(3,2) DEFAULT 0.00,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Citizens table
CREATE TABLE IF NOT EXISTS citizens (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  date_of_birth DATE,
  gender VARCHAR(10),
  blood_group VARCHAR(5),
  emergency_contact VARCHAR(20),
  medical_history JSONB,
  insurance_details JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health Records table
CREATE TABLE IF NOT EXISTS health_records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  citizen_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
  asha_id UUID REFERENCES asha_workers(id),
  record_type VARCHAR(50) NOT NULL,
  diagnosis JSONB,
  symptoms JSONB,
  vital_signs JSONB,
  medications JSONB,
  lab_results JSONB,
  recommendations TEXT,
  risk_level VARCHAR(20),
  follow_up_date DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI Diagnoses table
CREATE TABLE IF NOT EXISTS ai_diagnoses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  health_record_id UUID REFERENCES health_records(id) ON DELETE CASCADE,
  model_used VARCHAR(100),
  input_data JSONB,
  prediction_results JSONB,
  confidence_score DECIMAL(5,4),
  processing_time_ms INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Government Schemes table
CREATE TABLE IF NOT EXISTS government_schemes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  citizen_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
  scheme_name VARCHAR(100) NOT NULL,
  scheme_id VARCHAR(50),
  eligibility_status VARCHAR(20),
  application_status VARCHAR(20),
  benefits_availed JSONB,
  documents_submitted JSONB,
  approved_amount DECIMAL(10,2),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insurance Policies table
CREATE TABLE IF NOT EXISTS insurance_policies (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  citizen_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
  policy_type VARCHAR(50),
  policy_number VARCHAR(100) UNIQUE,
  premium_amount DECIMAL(10,2),
  coverage_amount DECIMAL(10,2),
  start_date DATE,
  end_date DATE,
  status VARCHAR(20) DEFAULT 'active',
  claims JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Emergency Alerts table
CREATE TABLE IF NOT EXISTS emergency_alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  citizen_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
  alert_type VARCHAR(50) NOT NULL,
  severity VARCHAR(20) NOT NULL,
  location JSONB,
  description TEXT,
  status VARCHAR(20) DEFAULT 'active',
  responder_id UUID REFERENCES asha_workers(id),
  response_time TIMESTAMP WITH TIME ZONE,
  resolution_time TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Healthcare Facilities table
CREATE TABLE IF NOT EXISTS healthcare_facilities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL,
  address TEXT,
  district VARCHAR(100),
  block VARCHAR(100),
  coordinates JSONB,
  contact_info JSONB,
  services JSONB,
  bsky_empanelled BOOLEAN DEFAULT false,
  operating_hours JSONB,
  rating DECIMAL(2,1),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat Sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  session_data JSONB,
  language VARCHAR(10) DEFAULT 'en',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE asha_workers ENABLE ROW LEVEL SECURITY;
ALTER TABLE citizens ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_diagnoses ENABLE ROW LEVEL SECURITY;
ALTER TABLE government_schemes ENABLE ROW LEVEL SECURITY;
ALTER TABLE insurance_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE emergency_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE healthcare_facilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Users
CREATE POLICY "Users can read own data" ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON users
  FOR UPDATE USING (auth.uid() = id);

-- RLS Policies for ASHA Workers
CREATE POLICY "ASHA workers can read own data" ON asha_workers
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "ASHA workers can update own data" ON asha_workers
  FOR UPDATE USING (auth.uid() = user_id);

-- RLS Policies for Citizens
CREATE POLICY "Citizens can read own data" ON citizens
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Citizens can update own data" ON citizens
  FOR UPDATE USING (auth.uid() = user_id);

-- RLS Policies for Health Records
CREATE POLICY "Citizens can read own health records" ON health_records
  FOR SELECT USING (
    auth.uid() IN (
      SELECT user_id FROM citizens WHERE id = health_records.citizen_id
    )
  );

CREATE POLICY "ASHA workers can read assigned patients' records" ON health_records
  FOR SELECT USING (
    auth.uid() IN (
      SELECT aw.user_id FROM asha_workers aw
      JOIN citizens c ON health_records.citizen_id = c.id
      JOIN users u ON c.user_id = u.id
      WHERE u.village = ANY(aw.assigned_villages)
    )
  );

CREATE POLICY "ASHA workers can create health records" ON health_records
  FOR INSERT WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM asha_workers WHERE id = health_records.asha_id
    )
  );

-- RLS Policies for AI Diagnoses
CREATE POLICY "Users can read own AI diagnoses" ON ai_diagnoses
  FOR SELECT USING (
    health_record_id IN (
      SELECT hr.id FROM health_records hr
      JOIN citizens c ON hr.citizen_id = c.id
      WHERE c.user_id = auth.uid()
    )
  );

-- RLS Policies for Government Schemes
CREATE POLICY "Citizens can read own schemes" ON government_schemes
  FOR SELECT USING (
    auth.uid() IN (
      SELECT user_id FROM citizens WHERE id = government_schemes.citizen_id
    )
  );

CREATE POLICY "Citizens can create scheme applications" ON government_schemes
  FOR INSERT WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM citizens WHERE id = government_schemes.citizen_id
    )
  );

-- RLS Policies for Insurance Policies
CREATE POLICY "Citizens can read own policies" ON insurance_policies
  FOR SELECT USING (
    auth.uid() IN (
      SELECT user_id FROM citizens WHERE id = insurance_policies.citizen_id
    )
  );

CREATE POLICY "Citizens can create policies" ON insurance_policies
  FOR INSERT WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM citizens WHERE id = insurance_policies.citizen_id
    )
  );

-- RLS Policies for Emergency Alerts
CREATE POLICY "Citizens can read own alerts" ON emergency_alerts
  FOR SELECT USING (
    auth.uid() IN (
      SELECT user_id FROM citizens WHERE id = emergency_alerts.citizen_id
    )
  );

CREATE POLICY "ASHA workers can read assigned area alerts" ON emergency_alerts
  FOR SELECT USING (
    auth.uid() IN (
      SELECT aw.user_id FROM asha_workers aw
      JOIN citizens c ON emergency_alerts.citizen_id = c.id
      JOIN users u ON c.user_id = u.id
      WHERE u.village = ANY(aw.assigned_villages)
    )
  );

CREATE POLICY "Citizens can create alerts" ON emergency_alerts
  FOR INSERT WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM citizens WHERE id = emergency_alerts.citizen_id
    )
  );

-- RLS Policies for Healthcare Facilities
CREATE POLICY "Anyone can read healthcare facilities" ON healthcare_facilities
  FOR SELECT USING (true);

CREATE POLICY "ASHA workers can add facilities" ON healthcare_facilities
  FOR INSERT WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM users WHERE user_type = 'asha'
    )
  );

-- RLS Policies for Chat Sessions
CREATE POLICY "Users can read own chat sessions" ON chat_sessions
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create chat sessions" ON chat_sessions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own chat sessions" ON chat_sessions
  FOR UPDATE USING (auth.uid() = user_id);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_abha_id ON users(abha_id);
CREATE INDEX IF NOT EXISTS idx_users_district ON users(district);
CREATE INDEX IF NOT EXISTS idx_asha_workers_user_id ON asha_workers(user_id);
CREATE INDEX IF NOT EXISTS idx_citizens_user_id ON citizens(user_id);
CREATE INDEX IF NOT EXISTS idx_health_records_citizen_id ON health_records(citizen_id);
CREATE INDEX IF NOT EXISTS idx_health_records_created_at ON health_records(created_at);
CREATE INDEX IF NOT EXISTS idx_emergency_alerts_status ON emergency_alerts(status);
CREATE INDEX IF NOT EXISTS idx_emergency_alerts_created_at ON emergency_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_facilities_district ON healthcare_facilities(district);
CREATE INDEX IF NOT EXISTS idx_facilities_type ON healthcare_facilities(type);
CREATE INDEX IF NOT EXISTS idx_facilities_bsky ON healthcare_facilities(bsky_empanelled);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);

-- Insert Demo Data
INSERT INTO users (id, email, user_type, full_name, phone, district, block, village, abha_id) VALUES
  ('550e8400-e29b-41d4-a716-446655440001', 'asha@demo.com', 'asha', 'Priya Patel', '+91 9876543210', 'Koraput', 'Koraput', 'Kendrapara', NULL),
  ('550e8400-e29b-41d4-a716-446655440002', 'citizen@demo.com', 'citizen', 'Ramesh Kumar', '+91 9876543211', 'Koraput', 'Koraput', 'Bhadrak', '12-3456-7890-1234')
ON CONFLICT (email) DO NOTHING;

INSERT INTO asha_workers (user_id, asha_id, certification_number, assigned_villages, training_status, performance_score) VALUES
  ('550e8400-e29b-41d4-a716-446655440001', 'ASHA001', 'CERT2024001', ARRAY['Kendrapara', 'Bhadrak'], 'completed', 4.8)
ON CONFLICT (asha_id) DO NOTHING;

INSERT INTO citizens (user_id, date_of_birth, gender, blood_group, emergency_contact) VALUES
  ('550e8400-e29b-41d4-a716-446655440002', '1985-05-15', 'Male', 'B+', '+91 9876543212')
ON CONFLICT (user_id) DO NOTHING;

-- Insert Sample Healthcare Facilities
INSERT INTO healthcare_facilities (name, type, address, district, block, coordinates, contact_info, services, bsky_empanelled, operating_hours, rating) VALUES
  ('PHC Koraput', 'phc', 'Main Road, Koraput, Odisha', 'Koraput', 'Koraput', '{"lat": 18.8137, "lng": 82.7119}', '{"phone": "+91 9876543210", "email": "phc.koraput@gov.in"}', '["General Medicine", "Maternal Care", "Vaccination", "Basic Diagnostics"]', true, '{"24x7": true}', 4.2),
  ('District Hospital Koraput', 'hospital', 'Hospital Road, Koraput, Odisha', 'Koraput', 'Koraput', '{"lat": 18.8137, "lng": 82.7119}', '{"phone": "+91 9876543211", "email": "dh.koraput@gov.in"}', '["Emergency Care", "Surgery", "ICU", "Specialist Care"]', true, '{"24x7": true}', 4.5),
  ('CHC Jeypore', 'chc', 'Jeypore, Koraput District, Odisha', 'Koraput', 'Jeypore', '{"lat": 18.8564, "lng": 82.5742}', '{"phone": "+91 9876543212"}', '["Specialist Care", "Lab Services", "X-Ray"]', true, '{"open": "6:00", "close": "22:00"}', 4.0)
ON CONFLICT DO NOTHING;