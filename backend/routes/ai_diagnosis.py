from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import asyncio
import json
from datetime import datetime
import uuid

from services.ai_service import ai_service
from models.database import db

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/analyze-symptoms', methods=['POST'])
@jwt_required()
def analyze_symptoms():
    """Analyze symptoms using AI"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('symptoms'):
            return jsonify({'error': 'Symptoms data is required'}), 400
        
        # Extract data
        symptoms_data = data['symptoms']
        vital_signs = data.get('vital_signs')
        patient_history = data.get('patient_history')
        
        # Run AI analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            analysis_result = loop.run_until_complete(
                ai_service.analyze_symptoms(symptoms_data, vital_signs, user_id)
            )
        finally:
            loop.close()
        
        # Save health record
        health_record_id = save_health_record(
            user_id, symptoms_data, vital_signs, analysis_result, patient_history
        )
        
        # Update analysis result with health record ID
        analysis_result['health_record_id'] = health_record_id
        
        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Symptom analysis failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Analysis failed',
            'message': 'Please consult with your ASHA worker'
        }), 500

@ai_bp.route('/voice-analysis', methods=['POST'])
@jwt_required()
def voice_analysis():
    """Analyze voice input for symptoms"""
    try:
        user_id = get_jwt_identity()
        
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({'error': 'Audio file is required'}), 400
        
        audio_file = request.files['audio']
        language = request.form.get('language', 'hi')  # Default to Hindi
        
        # Process audio file (mock implementation)
        # In production, use speech-to-text service
        transcribed_text = process_audio_file(audio_file, language)
        
        if not transcribed_text:
            return jsonify({'error': 'Could not process audio'}), 400
        
        # Convert transcribed text to symptoms data
        symptoms_data = extract_symptoms_from_text(transcribed_text, language)
        
        # Run AI analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            analysis_result = loop.run_until_complete(
                ai_service.analyze_symptoms(symptoms_data, None, user_id)
            )
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'transcribed_text': transcribed_text,
            'extracted_symptoms': symptoms_data,
            'analysis': analysis_result,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Voice analysis failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Voice analysis failed'
        }), 500

@ai_bp.route('/vital-signs', methods=['POST'])
@jwt_required()
def process_vital_signs():
    """Process vital signs from IoT devices"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate vital signs data
        required_vitals = ['device_type', 'readings']
        for field in required_vitals:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        device_type = data['device_type']
        readings = data['readings']
        
        # Process based on device type
        processed_vitals = process_device_readings(device_type, readings)
        
        # Analyze vital signs for risk assessment
        risk_assessment = assess_vital_signs_risk(processed_vitals)
        
        # Save vital signs record
        vital_record_id = save_vital_signs_record(user_id, device_type, processed_vitals, risk_assessment)
        
        return jsonify({
            'success': True,
            'vital_record_id': vital_record_id,
            'processed_vitals': processed_vitals,
            'risk_assessment': risk_assessment,
            'recommendations': generate_vital_recommendations(risk_assessment),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Vital signs processing failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Vital signs processing failed'
        }), 500

@ai_bp.route('/diagnosis-history', methods=['GET'])
@jwt_required()
def get_diagnosis_history():
    """Get AI diagnosis history for user"""
    try:
        user_id = get_jwt_identity()
        
        # Get user's health records with AI diagnoses
        query = """
        SELECT hr.*, ad.model_used, ad.prediction_results, ad.confidence_score,
               ad.created_at as diagnosis_date
        FROM health_records hr
        LEFT JOIN ai_diagnoses ad ON hr.id = ad.health_record_id
        JOIN citizens c ON hr.citizen_id = c.id
        WHERE c.user_id = %s
        ORDER BY hr.created_at DESC
        LIMIT 50
        """
        
        records = db.execute_query(query, (user_id,))
        
        # Format records
        formatted_records = []
        for record in records:
            formatted_record = {
                'id': record['id'],
                'record_type': record['record_type'],
                'diagnosis': json.loads(record['diagnosis']) if record['diagnosis'] else {},
                'symptoms': json.loads(record['symptoms']) if record['symptoms'] else {},
                'vital_signs': json.loads(record['vital_signs']) if record['vital_signs'] else {},
                'risk_level': record['risk_level'],
                'recommendations': record['recommendations'],
                'created_at': record['created_at'].isoformat(),
                'ai_analysis': {
                    'model_used': record['model_used'],
                    'predictions': json.loads(record['prediction_results']) if record['prediction_results'] else {},
                    'confidence_score': float(record['confidence_score']) if record['confidence_score'] else 0.0,
                    'diagnosis_date': record['diagnosis_date'].isoformat() if record['diagnosis_date'] else None
                }
            }
            formatted_records.append(formatted_record)
        
        return jsonify({
            'success': True,
            'records': formatted_records,
            'total_count': len(formatted_records)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Diagnosis history fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch diagnosis history'
        }), 500

def save_health_record(user_id, symptoms_data, vital_signs, analysis_result, patient_history):
    """Save health record to database"""
    try:
        # Get citizen ID
        citizen_query = "SELECT id FROM citizens WHERE user_id = %s"
        citizen_result = db.execute_query(citizen_query, (user_id,))
        
        if not citizen_result:
            return None
        
        citizen_id = citizen_result[0]['id']
        record_id = str(uuid.uuid4())
        
        # Prepare diagnosis data
        diagnosis_data = {
            'condition': analysis_result.get('predictions', {}).get('condition', 'unknown'),
            'confidence': analysis_result.get('confidence_score', 0.0),
            'ai_analysis': analysis_result.get('predictions', {})
        }
        
        # Insert health record
        query = """
        INSERT INTO health_records (id, citizen_id, record_type, diagnosis, symptoms, 
                                  vital_signs, recommendations, risk_level, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            record_id,
            citizen_id,
            'ai_diagnosis',
            json.dumps(diagnosis_data),
            json.dumps(symptoms_data),
            json.dumps(vital_signs) if vital_signs else None,
            '\n'.join(analysis_result.get('recommendations', [])),
            analysis_result.get('risk_level', 'unknown'),
            datetime.utcnow()
        )
        
        db.execute_query(query, params)
        
        # Update AI diagnosis record with health record ID
        if analysis_result.get('diagnosis_id'):
            update_query = "UPDATE ai_diagnoses SET health_record_id = %s WHERE id = %s"
            db.execute_query(update_query, (record_id, analysis_result['diagnosis_id']))
        
        return record_id
        
    except Exception as e:
        current_app.logger.error(f"Health record save failed: {str(e)}")
        return None

def process_audio_file(audio_file, language):
    """Process audio file and convert to text"""
    try:
        # Mock implementation - replace with actual speech-to-text
        # In production, use services like Google Speech-to-Text, Azure Speech, etc.
        
        mock_transcriptions = {
            'hi': 'मुझे बुखार और सिरदर्द है। मैं बहुत कमजोर महसूस कर रहा हूं।',
            'en': 'I have fever and headache. I am feeling very weak.',
            'or': 'ମୋର ଜ୍ୱର ଓ ମୁଣ୍ଡବିନ୍ଧା ହେଉଛି। ମୁଁ ବହୁତ ଦୁର୍ବଳ ଲାଗୁଛି।'
        }
        
        return mock_transcriptions.get(language, mock_transcriptions['en'])
        
    except Exception as e:
        current_app.logger.error(f"Audio processing failed: {str(e)}")
        return None

def extract_symptoms_from_text(text, language):
    """Extract symptoms from transcribed text"""
    try:
        # Mock implementation - replace with actual NLP processing
        symptom_keywords = {
            'hi': {
                'बुखार': 'fever',
                'सिरदर्द': 'headache',
                'कमजोर': 'weakness',
                'खांसी': 'cough',
                'सांस': 'breathing_difficulty'
            },
            'en': {
                'fever': 'fever',
                'headache': 'headache',
                'weak': 'weakness',
                'cough': 'cough',
                'breathing': 'breathing_difficulty'
            }
        }
        
        keywords = symptom_keywords.get(language, symptom_keywords['en'])
        extracted_symptoms = []
        
        text_lower = text.lower()
        for keyword, symptom in keywords.items():
            if keyword in text_lower:
                extracted_symptoms.append(symptom)
        
        return {
            'primary_symptoms': extracted_symptoms,
            'original_text': text,
            'language': language
        }
        
    except Exception as e:
        current_app.logger.error(f"Symptom extraction failed: {str(e)}")
        return {'primary_symptoms': [], 'original_text': text, 'language': language}

def process_device_readings(device_type, readings):
    """Process readings from IoT devices"""
    try:
        processed = {}
        
        if device_type == 'digital_stethoscope':
            processed = {
                'heart_rate': readings.get('heart_rate'),
                'heart_rhythm': readings.get('rhythm', 'regular'),
                'lung_sounds': readings.get('lung_sounds', 'clear'),
                'device_type': device_type
            }
        elif device_type == 'hemoglobin_meter':
            processed = {
                'hemoglobin': readings.get('hemoglobin'),
                'hematocrit': readings.get('hematocrit'),
                'device_type': device_type
            }
        elif device_type == 'bp_monitor':
            processed = {
                'systolic_bp': readings.get('systolic'),
                'diastolic_bp': readings.get('diastolic'),
                'pulse': readings.get('pulse'),
                'device_type': device_type
            }
        
        return processed
        
    except Exception as e:
        current_app.logger.error(f"Device reading processing failed: {str(e)}")
        return {}

def assess_vital_signs_risk(vital_signs):
    """Assess risk level based on vital signs"""
    try:
        risk_level = 'normal'
        risk_factors = []
        
        # Blood pressure assessment
        if 'systolic_bp' in vital_signs and 'diastolic_bp' in vital_signs:
            systolic = vital_signs['systolic_bp']
            diastolic = vital_signs['diastolic_bp']
            
            if systolic >= 180 or diastolic >= 120:
                risk_level = 'critical'
                risk_factors.append('Severe hypertension')
            elif systolic >= 140 or diastolic >= 90:
                risk_level = 'high' if risk_level != 'critical' else risk_level
                risk_factors.append('Hypertension')
        
        # Hemoglobin assessment
        if 'hemoglobin' in vital_signs:
            hb = vital_signs['hemoglobin']
            if hb < 7:
                risk_level = 'critical'
                risk_factors.append('Severe anemia')
            elif hb < 10:
                risk_level = 'high' if risk_level not in ['critical'] else risk_level
                risk_factors.append('Moderate anemia')
            elif hb < 12:
                risk_level = 'medium' if risk_level == 'normal' else risk_level
                risk_factors.append('Mild anemia')
        
        # Heart rate assessment
        if 'heart_rate' in vital_signs:
            hr = vital_signs['heart_rate']
            if hr < 50 or hr > 120:
                risk_level = 'high' if risk_level not in ['critical'] else risk_level
                risk_factors.append('Abnormal heart rate')
        
        return {
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'assessment_date': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        current_app.logger.error(f"Risk assessment failed: {str(e)}")
        return {'risk_level': 'unknown', 'risk_factors': []}

def generate_vital_recommendations(risk_assessment):
    """Generate recommendations based on vital signs risk"""
    try:
        recommendations = []
        risk_level = risk_assessment.get('risk_level', 'normal')
        
        if risk_level == 'critical':
            recommendations.extend([
                'Seek immediate medical attention',
                'Call emergency services (108)',
                'Contact ASHA worker immediately'
            ])
        elif risk_level == 'high':
            recommendations.extend([
                'Consult healthcare provider within 24 hours',
                'Monitor vital signs closely',
                'Contact ASHA worker for guidance'
            ])
        elif risk_level == 'medium':
            recommendations.extend([
                'Schedule appointment with healthcare provider',
                'Monitor symptoms for changes',
                'Follow up with ASHA worker'
            ])
        else:
            recommendations.extend([
                'Continue regular health monitoring',
                'Maintain healthy lifestyle',
                'Regular check-ups with ASHA worker'
            ])
        
        return recommendations
        
    except Exception as e:
        current_app.logger.error(f"Recommendation generation failed: {str(e)}")
        return ['Consult with healthcare provider']

def save_vital_signs_record(user_id, device_type, vital_signs, risk_assessment):
    """Save vital signs record"""
    try:
        record_id = str(uuid.uuid4())
        
        # Get citizen ID
        citizen_query = "SELECT id FROM citizens WHERE user_id = %s"
        citizen_result = db.execute_query(citizen_query, (user_id,))
        
        if not citizen_result:
            return None
        
        citizen_id = citizen_result[0]['id']
        
        # Save as health record
        query = """
        INSERT INTO health_records (id, citizen_id, record_type, vital_signs, 
                                  risk_level, recommendations, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            record_id,
            citizen_id,
            f'vital_signs_{device_type}',
            json.dumps(vital_signs),
            risk_assessment.get('risk_level', 'unknown'),
            '\n'.join(generate_vital_recommendations(risk_assessment)),
            datetime.utcnow()
        )
        
        db.execute_query(query, params)
        return record_id
        
    except Exception as e:
        current_app.logger.error(f"Vital signs record save failed: {str(e)}")
        return None