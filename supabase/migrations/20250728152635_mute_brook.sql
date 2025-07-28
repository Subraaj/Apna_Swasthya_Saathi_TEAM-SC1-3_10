/*
  # Demo Data for Apna Swasthya Saathi

  1. Sample Health Records
    - AI diagnosis records for demo citizen
    - Various health conditions and risk levels
    - Medication and treatment history

  2. Sample Emergency Alerts
    - Different types of emergency situations
    - Response tracking

  3. Sample Insurance Policies
    - Active insurance policies
    - Claims history

  4. Sample Chat Sessions
    - Health consultation conversations
    - AI responses and recommendations
*/

-- Sample Health Records for Demo Citizen
DO $$
DECLARE
    demo_citizen_id UUID;
    demo_asha_id UUID;
    health_record_id UUID;
BEGIN
    -- Get demo citizen and ASHA IDs
    SELECT id INTO demo_citizen_id FROM citizens WHERE user_id = '550e8400-e29b-41d4-a716-446655440002';
    SELECT id INTO demo_asha_id FROM asha_workers WHERE user_id = '550e8400-e29b-41d4-a716-446655440001';
    
    IF demo_citizen_id IS NOT NULL AND demo_asha_id IS NOT NULL THEN
        -- Insert sample health records
        INSERT INTO health_records (id, citizen_id, asha_id, record_type, diagnosis, symptoms, vital_signs, recommendations, risk_level, created_at) VALUES
        (uuid_generate_v4(), demo_citizen_id, demo_asha_id, 'ai_diagnosis', 
         '{"condition": "anemia", "confidence": 0.85, "ai_analysis": {"hemoglobin_level": 7.2}}',
         '["fatigue", "weakness", "pale_skin"]',
         '{"hemoglobin": 7.2, "blood_pressure": "120/80", "heart_rate": 85}',
         'Iron supplementation recommended. Follow-up in 2 weeks. Dietary counseling needed.',
         'high',
         NOW() - INTERVAL '5 days'),
        
        (uuid_generate_v4(), demo_citizen_id, demo_asha_id, 'prescription',
         '{"medication": "Iron + Folic Acid", "dosage": "1 tablet daily", "duration": "3 months"}',
         '["anemia", "iron_deficiency"]',
         NULL,
         'Take with vitamin C for better absorption. Avoid tea/coffee with medication.',
         'medium',
         NOW() - INTERVAL '3 days'),
         
        (uuid_generate_v4(), demo_citizen_id, demo_asha_id, 'follow_up',
         '{"improvement": "moderate", "hemoglobin": 8.5, "compliance": "good"}',
         '["improved_energy", "less_fatigue"]',
         '{"hemoglobin": 8.5, "blood_pressure": "118/78", "heart_rate": 78}',
         'Continue iron supplementation. Hemoglobin improving. Next check in 4 weeks.',
         'low',
         NOW() - INTERVAL '1 day');
    END IF;
END $$;

-- Sample Insurance Policy for Demo Citizen
DO $$
DECLARE
    demo_citizen_id UUID;
BEGIN
    SELECT id INTO demo_citizen_id FROM citizens WHERE user_id = '550e8400-e29b-41d4-a716-446655440002';
    
    IF demo_citizen_id IS NOT NULL THEN
        INSERT INTO insurance_policies (citizen_id, policy_type, policy_number, premium_amount, coverage_amount, start_date, end_date, status, claims) VALUES
        (demo_citizen_id, 'basic_health', 'ASS20240115001', 600.00, 5000.00, 
         CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '11 months', 'active',
         '[{"claim_id": "CLM001", "claim_type": "hospitalization", "amount": 1500, "status": "approved", "date": "2024-01-10"}]');
    END IF;
END $$;

-- Sample Emergency Alert
DO $$
DECLARE
    demo_citizen_id UUID;
    demo_asha_id UUID;
BEGIN
    SELECT id INTO demo_citizen_id FROM citizens WHERE user_id = '550e8400-e29b-41d4-a716-446655440002';
    SELECT id INTO demo_asha_id FROM asha_workers WHERE user_id = '550e8400-e29b-41d4-a716-446655440001';
    
    IF demo_citizen_id IS NOT NULL THEN
        INSERT INTO emergency_alerts (citizen_id, alert_type, severity, location, description, status, responder_id, response_time, created_at) VALUES
        (demo_citizen_id, 'medical', 'medium', 
         '{"latitude": 18.8137, "longitude": 82.7119, "address": "Koraput, Odisha"}',
         'Patient experiencing severe weakness and dizziness',
         'resolved', demo_asha_id, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '6 hours');
    END IF;
END $$;

-- Sample Government Scheme Application
DO $$
DECLARE
    demo_citizen_id UUID;
BEGIN
    SELECT id INTO demo_citizen_id FROM citizens WHERE user_id = '550e8400-e29b-41d4-a716-446655440002';
    
    IF demo_citizen_id IS NOT NULL THEN
        INSERT INTO government_schemes (citizen_id, scheme_name, scheme_id, eligibility_status, application_status, benefits_availed, approved_amount) VALUES
        (demo_citizen_id, 'BSKY', 'BSKY2024001', 'eligible', 'approved', 
         '{"coverage_amount": 500000, "family_members": 4, "empanelled_hospitals": 25}', 500000.00);
    END IF;
END $$;

-- Sample Chat Session
DO $$
DECLARE
    demo_user_id UUID := '550e8400-e29b-41d4-a716-446655440002';
    session_data JSONB;
BEGIN
    session_data := '{
        "session_type": "health_consultation",
        "language": "en",
        "messages": [
            {
                "id": "msg1",
                "type": "assistant",
                "content": "Hello! I am your AI health assistant. How can I help you today?",
                "timestamp": "2024-01-15T10:00:00Z"
            },
            {
                "id": "msg2", 
                "type": "user",
                "content": "I have been feeling very tired and weak lately",
                "timestamp": "2024-01-15T10:01:00Z"
            },
            {
                "id": "msg3",
                "type": "assistant", 
                "content": "I understand you are experiencing fatigue and weakness. These could be symptoms of anemia, which is common in your area. Have you noticed any other symptoms like pale skin or shortness of breath?",
                "timestamp": "2024-01-15T10:01:30Z",
                "suggestions": ["Yes, I have pale skin", "No other symptoms", "I also have headaches"]
            }
        ],
        "context": {
            "user_symptoms": ["fatigue", "weakness"],
            "current_topic": "symptom_assessment",
            "assessment_stage": "gathering_info"
        }
    }';
    
    INSERT INTO chat_sessions (user_id, session_data, language, created_at, updated_at) VALUES
    (demo_user_id, session_data, 'en', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour');
END $$;

-- Additional Healthcare Facilities
INSERT INTO healthcare_facilities (name, type, address, district, block, coordinates, contact_info, services, bsky_empanelled, operating_hours, rating) VALUES
('Apollo Clinic Koraput', 'private', 'Market Street, Koraput, Odisha', 'Koraput', 'Koraput', 
 '{"lat": 18.8137, "lng": 82.7119}', '{"phone": "+91 9876543213", "email": "apollo.koraput@apollo.com"}',
 '["General Medicine", "Cardiology", "Pediatrics", "Diagnostics"]', false, 
 '{"open": "9:00", "close": "21:00"}', 4.8),

('Kalinga Hospital', 'private', 'Hospital Road, Jeypore, Odisha', 'Koraput', 'Jeypore',
 '{"lat": 18.8564, "lng": 82.5742}', '{"phone": "+91 9876543214", "emergency": "+91 9876543215"}',
 '["Emergency Care", "Surgery", "ICU", "Maternity", "Pediatrics"]', true,
 '{"24x7": true}', 4.6),

('PHC Rayagada', 'phc', 'Main Road, Rayagada, Odisha', 'Rayagada', 'Rayagada',
 '{"lat": 19.1672, "lng": 83.4156}', '{"phone": "+91 9876543216"}',
 '["General Medicine", "Maternal Care", "Child Health", "Vaccination"]', true,
 '{"open": "8:00", "close": "20:00"}', 4.1)
ON CONFLICT DO NOTHING;

-- Sample AI Diagnoses linked to Health Records
DO $$
DECLARE
    health_record_rec RECORD;
BEGIN
    FOR health_record_rec IN 
        SELECT id FROM health_records WHERE record_type = 'ai_diagnosis' LIMIT 3
    LOOP
        INSERT INTO ai_diagnoses (health_record_id, model_used, input_data, prediction_results, confidence_score, processing_time_ms) VALUES
        (health_record_rec.id, 'gemini_1.5_flash', 
         '{"symptoms": ["fatigue", "weakness", "pale_skin"], "vital_signs": {"hemoglobin": 7.2}}',
         '{"condition": "anemia", "risk_factors": ["poor_nutrition", "iron_deficiency"], "recommendations": ["iron_supplements", "dietary_changes"]}',
         0.85, 1200);
    END LOOP;
END $$;