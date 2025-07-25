from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import uuid
from datetime import datetime, timedelta

from models.database import db
from models.user import User, Citizen

records_bp = Blueprint('records', __name__)

@records_bp.route('/', methods=['GET'])
@jwt_required()
def get_health_records():
    """Get user's health records"""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        record_type = request.args.get('type', 'all')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get citizen data
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Build query
        base_query = """
        SELECT hr.*, ad.model_used, ad.prediction_results, ad.confidence_score,
               ad.created_at as ai_diagnosis_date
        FROM health_records hr
        LEFT JOIN ai_diagnoses ad ON hr.id = ad.health_record_id
        WHERE hr.citizen_id = %s
        """
        
        params = [citizen['id']]
        
        # Add filters
        if record_type != 'all':
            base_query += " AND hr.record_type = %s"
            params.append(record_type)
        
        if start_date:
            base_query += " AND hr.created_at >= %s"
            params.append(start_date)
        
        if end_date:
            base_query += " AND hr.created_at <= %s"
            params.append(end_date)
        
        base_query += " ORDER BY hr.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        records = db.execute_query(base_query, params)
        
        # Format records
        formatted_records = []
        for record in records:
            formatted_record = format_health_record(record)
            formatted_records.append(formatted_record)
        
        # Get total count
        count_query = """
        SELECT COUNT(*) as total FROM health_records hr
        WHERE hr.citizen_id = %s
        """
        count_params = [citizen['id']]
        
        if record_type != 'all':
            count_query += " AND hr.record_type = %s"
            count_params.append(record_type)
        
        if start_date:
            count_query += " AND hr.created_at >= %s"
            count_params.append(start_date)
        
        if end_date:
            count_query += " AND hr.created_at <= %s"
            count_params.append(end_date)
        
        total_count = db.execute_query(count_query, count_params)[0]['total']
        
        return jsonify({
            'success': True,
            'records': formatted_records,
            'pagination': {
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count
            },
            'filters': {
                'record_type': record_type,
                'start_date': start_date,
                'end_date': end_date
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Health records fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch health records'
        }), 500

@records_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_health_summary():
    """Get health summary for user"""
    try:
        user_id = get_jwt_identity()
        
        # Get citizen data
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Get recent records summary
        recent_query = """
        SELECT record_type, COUNT(*) as count, MAX(created_at) as latest_date
        FROM health_records 
        WHERE citizen_id = %s AND created_at >= %s
        GROUP BY record_type
        """
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_records = db.execute_query(recent_query, (citizen['id'], thirty_days_ago))
        
        # Get latest vital signs
        vitals_query = """
        SELECT vital_signs, created_at
        FROM health_records 
        WHERE citizen_id = %s AND vital_signs IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        latest_vitals = db.execute_query(vitals_query, (citizen['id'],))
        
        # Get risk assessments
        risk_query = """
        SELECT risk_level, COUNT(*) as count
        FROM health_records 
        WHERE citizen_id = %s AND risk_level IS NOT NULL
        GROUP BY risk_level
        """
        
        risk_distribution = db.execute_query(risk_query, (citizen['id'],))
        
        # Get medication history
        medication_query = """
        SELECT medications, created_at
        FROM health_records 
        WHERE citizen_id = %s AND medications IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 5
        """
        
        recent_medications = db.execute_query(medication_query, (citizen['id'],))
        
        # Format summary
        summary = {
            'patient_info': {
                'name': citizen.get('full_name', 'Unknown'),
                'age': calculate_age(citizen.get('date_of_birth')),
                'gender': citizen.get('gender'),
                'blood_group': citizen.get('blood_group'),
                'abha_id': citizen.get('abha_id')
            },
            'recent_activity': {
                'records_last_30_days': sum(r['count'] for r in recent_records),
                'record_types': [
                    {
                        'type': r['record_type'],
                        'count': r['count'],
                        'latest_date': r['latest_date'].isoformat()
                    } for r in recent_records
                ]
            },
            'latest_vitals': format_vital_signs(latest_vitals[0]) if latest_vitals else None,
            'risk_assessment': {
                'distribution': [
                    {
                        'risk_level': r['risk_level'],
                        'count': r['count']
                    } for r in risk_distribution
                ],
                'current_risk': get_current_risk_level(citizen['id'])
            },
            'medications': [
                {
                    'medications': json.loads(m['medications']) if m['medications'] else {},
                    'date': m['created_at'].isoformat()
                } for m in recent_medications
            ],
            'health_trends': get_health_trends(citizen['id']),
            'recommendations': get_health_recommendations(citizen['id'])
        }
        
        return jsonify({
            'success': True,
            'summary': summary,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Health summary generation failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate health summary'
        }), 500

@records_bp.route('/create', methods=['POST'])
@jwt_required()
def create_health_record():
    """Create new health record"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['record_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Get citizen data
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Create health record
        record_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO health_records (id, citizen_id, record_type, diagnosis, symptoms,
                                  vital_signs, medications, lab_results, recommendations,
                                  risk_level, follow_up_date, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            record_id,
            citizen['id'],
            data['record_type'],
            json.dumps(data.get('diagnosis', {})),
            json.dumps(data.get('symptoms', {})),
            json.dumps(data.get('vital_signs', {})),
            json.dumps(data.get('medications', {})),
            json.dumps(data.get('lab_results', {})),
            data.get('recommendations', ''),
            data.get('risk_level', 'unknown'),
            data.get('follow_up_date'),
            datetime.utcnow()
        )
        
        db.execute_query(query, params)
        
        return jsonify({
            'success': True,
            'message': 'Health record created successfully',
            'record_id': record_id,
            'record_type': data['record_type']
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Health record creation failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create health record'
        }), 500

@records_bp.route('/<record_id>', methods=['GET'])
@jwt_required()
def get_health_record(record_id):
    """Get specific health record"""
    try:
        user_id = get_jwt_identity()
        
        # Get citizen data
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Get record
        query = """
        SELECT hr.*, ad.model_used, ad.prediction_results, ad.confidence_score,
               ad.created_at as ai_diagnosis_date
        FROM health_records hr
        LEFT JOIN ai_diagnoses ad ON hr.id = ad.health_record_id
        WHERE hr.id = %s AND hr.citizen_id = %s
        """
        
        result = db.execute_query(query, (record_id, citizen['id']))
        
        if not result:
            return jsonify({'error': 'Health record not found'}), 404
        
        record = format_health_record(result[0])
        
        return jsonify({
            'success': True,
            'record': record
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Health record fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch health record'
        }), 500

@records_bp.route('/<record_id>', methods=['PUT'])
@jwt_required()
def update_health_record(record_id):
    """Update health record"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get citizen data
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Check if record exists and belongs to user
        check_query = "SELECT id FROM health_records WHERE id = %s AND citizen_id = %s"
        existing = db.execute_query(check_query, (record_id, citizen['id']))
        
        if not existing:
            return jsonify({'error': 'Health record not found'}), 404
        
        # Update record
        update_fields = []
        params = []
        
        if 'diagnosis' in data:
            update_fields.append('diagnosis = %s')
            params.append(json.dumps(data['diagnosis']))
        
        if 'symptoms' in data:
            update_fields.append('symptoms = %s')
            params.append(json.dumps(data['symptoms']))
        
        if 'vital_signs' in data:
            update_fields.append('vital_signs = %s')
            params.append(json.dumps(data['vital_signs']))
        
        if 'medications' in data:
            update_fields.append('medications = %s')
            params.append(json.dumps(data['medications']))
        
        if 'lab_results' in data:
            update_fields.append('lab_results = %s')
            params.append(json.dumps(data['lab_results']))
        
        if 'recommendations' in data:
            update_fields.append('recommendations = %s')
            params.append(data['recommendations'])
        
        if 'risk_level' in data:
            update_fields.append('risk_level = %s')
            params.append(data['risk_level'])
        
        if 'follow_up_date' in data:
            update_fields.append('follow_up_date = %s')
            params.append(data['follow_up_date'])
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        update_query = f"""
        UPDATE health_records 
        SET {', '.join(update_fields)}
        WHERE id = %s
        """
        params.append(record_id)
        
        db.execute_query(update_query, params)
        
        return jsonify({
            'success': True,
            'message': 'Health record updated successfully',
            'record_id': record_id
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Health record update failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update health record'
        }), 500

@records_bp.route('/export', methods=['GET'])
@jwt_required()
def export_health_records():
    """Export health records"""
    try:
        user_id = get_jwt_identity()
        export_format = request.args.get('format', 'json')
        
        # Get citizen data
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Get all records
        query = """
        SELECT hr.*, ad.model_used, ad.prediction_results, ad.confidence_score
        FROM health_records hr
        LEFT JOIN ai_diagnoses ad ON hr.id = ad.health_record_id
        WHERE hr.citizen_id = %s
        ORDER BY hr.created_at DESC
        """
        
        records = db.execute_query(query, (citizen['id'],))
        
        # Format records for export
        export_data = {
            'patient_info': {
                'name': citizen.get('full_name'),
                'abha_id': citizen.get('abha_id'),
                'date_of_birth': citizen.get('date_of_birth').isoformat() if citizen.get('date_of_birth') else None,
                'gender': citizen.get('gender'),
                'blood_group': citizen.get('blood_group')
            },
            'export_date': datetime.utcnow().isoformat(),
            'total_records': len(records),
            'records': [format_health_record(record) for record in records]
        }
        
        if export_format == 'json':
            return jsonify({
                'success': True,
                'export_data': export_data,
                'format': 'json'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported export format'
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Health records export failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to export health records'
        }), 500

@records_bp.route('/share', methods=['POST'])
@jwt_required()
def share_health_record():
    """Share health record with healthcare provider"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        record_id = data.get('record_id')
        recipient_type = data.get('recipient_type', 'doctor')
        recipient_id = data.get('recipient_id')
        access_duration_hours = data.get('access_duration_hours', 24)
        
        if not record_id:
            return jsonify({'error': 'Record ID is required'}), 400
        
        # Get citizen data
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Verify record ownership
        check_query = "SELECT id FROM health_records WHERE id = %s AND citizen_id = %s"
        existing = db.execute_query(check_query, (record_id, citizen['id']))
        
        if not existing:
            return jsonify({'error': 'Health record not found'}), 404
        
        # Generate sharing token (mock implementation)
        sharing_token = str(uuid.uuid4())
        expiry_time = datetime.utcnow() + timedelta(hours=access_duration_hours)
        
        # In production, store sharing permissions in database
        sharing_info = {
            'sharing_token': sharing_token,
            'record_id': record_id,
            'recipient_type': recipient_type,
            'recipient_id': recipient_id,
            'expires_at': expiry_time.isoformat(),
            'created_at': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': 'Health record shared successfully',
            'sharing_info': sharing_info,
            'access_url': f"/api/v1/records/shared/{sharing_token}"
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Health record sharing failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to share health record'
        }), 500

def format_health_record(record):
    """Format health record for API response"""
    try:
        formatted = {
            'id': record['id'],
            'record_type': record['record_type'],
            'diagnosis': json.loads(record['diagnosis']) if record['diagnosis'] else {},
            'symptoms': json.loads(record['symptoms']) if record['symptoms'] else {},
            'vital_signs': json.loads(record['vital_signs']) if record['vital_signs'] else {},
            'medications': json.loads(record['medications']) if record['medications'] else {},
            'lab_results': json.loads(record['lab_results']) if record['lab_results'] else {},
            'recommendations': record['recommendations'],
            'risk_level': record['risk_level'],
            'follow_up_date': record['follow_up_date'].isoformat() if record['follow_up_date'] else None,
            'created_at': record['created_at'].isoformat(),
            'ai_analysis': None
        }
        
        # Add AI analysis if available
        if record.get('model_used'):
            formatted['ai_analysis'] = {
                'model_used': record['model_used'],
                'predictions': json.loads(record['prediction_results']) if record['prediction_results'] else {},
                'confidence_score': float(record['confidence_score']) if record['confidence_score'] else 0.0,
                'analysis_date': record['ai_diagnosis_date'].isoformat() if record['ai_diagnosis_date'] else None
            }
        
        return formatted
        
    except Exception as e:
        current_app.logger.error(f"Health record formatting failed: {str(e)}")
        return record

def calculate_age(date_of_birth):
    """Calculate age from date of birth"""
    if not date_of_birth:
        return None
    
    try:
        today = datetime.now().date()
        if isinstance(date_of_birth, str):
            date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        
        age = today.year - date_of_birth.year
        if today.month < date_of_birth.month or (today.month == date_of_birth.month and today.day < date_of_birth.day):
            age -= 1
        
        return age
        
    except Exception:
        return None

def format_vital_signs(vitals_record):
    """Format vital signs data"""
    if not vitals_record:
        return None
    
    try:
        vital_signs = json.loads(vitals_record['vital_signs']) if vitals_record['vital_signs'] else {}
        
        return {
            'vital_signs': vital_signs,
            'recorded_at': vitals_record['created_at'].isoformat(),
            'summary': generate_vitals_summary(vital_signs)
        }
        
    except Exception:
        return None

def generate_vitals_summary(vital_signs):
    """Generate summary of vital signs"""
    summary = []
    
    if vital_signs.get('systolic_bp') and vital_signs.get('diastolic_bp'):
        bp = f"{vital_signs['systolic_bp']}/{vital_signs['diastolic_bp']}"
        summary.append(f"BP: {bp} mmHg")
    
    if vital_signs.get('heart_rate'):
        summary.append(f"HR: {vital_signs['heart_rate']} bpm")
    
    if vital_signs.get('temperature'):
        summary.append(f"Temp: {vital_signs['temperature']}°F")
    
    if vital_signs.get('hemoglobin'):
        summary.append(f"Hb: {vital_signs['hemoglobin']} g/dL")
    
    return ', '.join(summary) if summary else 'No vital signs recorded'

def get_current_risk_level(citizen_id):
    """Get current risk level for citizen"""
    try:
        query = """
        SELECT risk_level FROM health_records 
        WHERE citizen_id = %s AND risk_level IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        result = db.execute_query(query, (citizen_id,))
        return result[0]['risk_level'] if result else 'unknown'
        
    except Exception:
        return 'unknown'

def get_health_trends(citizen_id):
    """Get health trends for citizen"""
    try:
        # Get trends over last 6 months
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        query = """
        SELECT DATE_TRUNC('month', created_at) as month, 
               COUNT(*) as record_count,
               AVG(CASE WHEN risk_level = 'high' THEN 3 
                        WHEN risk_level = 'medium' THEN 2 
                        WHEN risk_level = 'low' THEN 1 
                        ELSE 0 END) as avg_risk_score
        FROM health_records 
        WHERE citizen_id = %s AND created_at >= %s
        GROUP BY DATE_TRUNC('month', created_at)
        ORDER BY month
        """
        
        trends = db.execute_query(query, (citizen_id, six_months_ago))
        
        return [
            {
                'month': trend['month'].strftime('%Y-%m'),
                'record_count': trend['record_count'],
                'avg_risk_score': float(trend['avg_risk_score']) if trend['avg_risk_score'] else 0
            } for trend in trends
        ]
        
    except Exception as e:
        current_app.logger.error(f"Health trends calculation failed: {str(e)}")
        return []

def get_health_recommendations(citizen_id):
    """Get health recommendations for citizen"""
    try:
        # Get recent risk levels and conditions
        query = """
        SELECT risk_level, diagnosis, recommendations
        FROM health_records 
        WHERE citizen_id = %s 
        ORDER BY created_at DESC
        LIMIT 5
        """
        
        recent_records = db.execute_query(query, (citizen_id,))
        
        recommendations = []
        
        # Analyze recent records for recommendations
        high_risk_count = sum(1 for r in recent_records if r['risk_level'] == 'high')
        
        if high_risk_count > 0:
            recommendations.append({
                'type': 'urgent',
                'message': 'You have recent high-risk health records. Please consult with your ASHA worker or healthcare provider.',
                'priority': 'high'
            })
        
        # Add general recommendations
        recommendations.extend([
            {
                'type': 'preventive',
                'message': 'Schedule regular health check-ups with your ASHA worker.',
                'priority': 'medium'
            },
            {
                'type': 'lifestyle',
                'message': 'Maintain a balanced diet and regular exercise routine.',
                'priority': 'low'
            },
            {
                'type': 'monitoring',
                'message': 'Keep track of your vital signs and symptoms.',
                'priority': 'medium'
            }
        ])
        
        return recommendations
        
    except Exception as e:
        current_app.logger.error(f"Health recommendations generation failed: {str(e)}")
        return []