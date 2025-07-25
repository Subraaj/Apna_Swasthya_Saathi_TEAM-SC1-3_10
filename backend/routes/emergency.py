from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import uuid
from datetime import datetime

from models.database import db
from models.user import User, Citizen, AshaWorker

emergency_bp = Blueprint('emergency', __name__)

@emergency_bp.route('/alert', methods=['POST'])
@jwt_required()
def create_emergency_alert():
    """Create emergency alert"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['alert_type', 'severity']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        alert_type = data['alert_type']
        severity = data['severity']
        description = data.get('description', '')
        location = data.get('location', {})
        
        # Get citizen data
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Create emergency alert
        alert_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO emergency_alerts (id, citizen_id, alert_type, severity, 
                                    location, description, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            alert_id,
            citizen['id'],
            alert_type,
            severity,
            json.dumps(location),
            description,
            'active',
            datetime.utcnow()
        )
        
        db.execute_query(query, params)
        
        # Find and notify nearby ASHA workers
        nearby_asha_workers = find_nearby_asha_workers(location, citizen)
        
        # Send notifications (mock implementation)
        notifications_sent = []
        for asha in nearby_asha_workers:
            notification_result = send_emergency_notification(asha, alert_id, alert_type, severity)
            if notification_result:
                notifications_sent.append(asha['full_name'])
        
        # Generate emergency response plan
        response_plan = generate_emergency_response_plan(alert_type, severity, location)
        
        return jsonify({
            'success': True,
            'alert_id': alert_id,
            'message': 'Emergency alert created successfully',
            'status': 'active',
            'notifications_sent': notifications_sent,
            'response_plan': response_plan,
            'emergency_contacts': get_emergency_contacts(),
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Emergency alert creation failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Emergency alert creation failed'
        }), 500

@emergency_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_user_alerts():
    """Get user's emergency alerts"""
    try:
        user_id = get_jwt_identity()
        
        # Get citizen data
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Get alerts
        query = """
        SELECT ea.*, aw.asha_id, u.full_name as responder_name
        FROM emergency_alerts ea
        LEFT JOIN asha_workers aw ON ea.responder_id = aw.id
        LEFT JOIN users u ON aw.user_id = u.id
        WHERE ea.citizen_id = %s
        ORDER BY ea.created_at DESC
        LIMIT 50
        """
        
        alerts = db.execute_query(query, (citizen['id'],))
        
        # Format alerts
        formatted_alerts = []
        for alert in alerts:
            formatted_alert = {
                'id': alert['id'],
                'alert_type': alert['alert_type'],
                'severity': alert['severity'],
                'description': alert['description'],
                'location': json.loads(alert['location']) if alert['location'] else {},
                'status': alert['status'],
                'responder': {
                    'asha_id': alert['asha_id'],
                    'name': alert['responder_name']
                } if alert['responder_id'] else None,
                'response_time': alert['response_time'].isoformat() if alert['response_time'] else None,
                'resolution_time': alert['resolution_time'].isoformat() if alert['resolution_time'] else None,
                'created_at': alert['created_at'].isoformat()
            }
            formatted_alerts.append(formatted_alert)
        
        return jsonify({
            'success': True,
            'alerts': formatted_alerts,
            'total_count': len(formatted_alerts),
            'active_alerts': len([a for a in formatted_alerts if a['status'] == 'active'])
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"User alerts fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch emergency alerts'
        }), 500

@emergency_bp.route('/respond/<alert_id>', methods=['POST'])
@jwt_required()
def respond_to_alert(alert_id):
    """ASHA worker responds to emergency alert"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        response_message = data.get('response_message', '')
        estimated_arrival = data.get('estimated_arrival_minutes', 15)
        
        # Get ASHA worker data
        asha = AshaWorker.get_by_user_id(user_id)
        if not asha:
            return jsonify({'error': 'ASHA worker profile not found'}), 404
        
        # Get alert
        alert_query = "SELECT * FROM emergency_alerts WHERE id = %s AND status = 'active'"
        alert_result = db.execute_query(alert_query, (alert_id,))
        
        if not alert_result:
            return jsonify({'error': 'Alert not found or already resolved'}), 404
        
        # Update alert with responder
        update_query = """
        UPDATE emergency_alerts 
        SET responder_id = %s, response_time = %s, status = %s
        WHERE id = %s
        """
        
        db.execute_query(update_query, (
            asha['id'],
            datetime.utcnow(),
            'responding',
            alert_id
        ))
        
        # Send response notification to citizen (mock implementation)
        citizen_notification = {
            'message': f"ASHA worker {asha['full_name']} is responding to your emergency",
            'estimated_arrival': f"{estimated_arrival} minutes",
            'contact': asha['phone'] if 'phone' in asha else 'Contact through ASHA supervisor'
        }
        
        return jsonify({
            'success': True,
            'message': 'Emergency response initiated',
            'alert_id': alert_id,
            'responder': {
                'name': asha['full_name'],
                'asha_id': asha['asha_id'],
                'estimated_arrival': estimated_arrival
            },
            'citizen_notification': citizen_notification
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Emergency response failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Emergency response failed'
        }), 500

@emergency_bp.route('/resolve/<alert_id>', methods=['POST'])
@jwt_required()
def resolve_alert(alert_id):
    """Resolve emergency alert"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        resolution_notes = data.get('resolution_notes', '')
        outcome = data.get('outcome', 'resolved')
        
        # Check if user is ASHA worker or the citizen who created the alert
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get alert
        if user['user_type'] == 'asha':
            # ASHA worker resolving
            asha = AshaWorker.get_by_user_id(user_id)
            alert_query = """
            SELECT * FROM emergency_alerts 
            WHERE id = %s AND responder_id = %s
            """
            alert_result = db.execute_query(alert_query, (alert_id, asha['id']))
        else:
            # Citizen resolving their own alert
            citizen = Citizen.get_by_user_id(user_id)
            alert_query = """
            SELECT * FROM emergency_alerts 
            WHERE id = %s AND citizen_id = %s
            """
            alert_result = db.execute_query(alert_query, (alert_id, citizen['id']))
        
        if not alert_result:
            return jsonify({'error': 'Alert not found or unauthorized'}), 404
        
        # Update alert status
        update_query = """
        UPDATE emergency_alerts 
        SET status = %s, resolution_time = %s
        WHERE id = %s
        """
        
        db.execute_query(update_query, (
            'resolved',
            datetime.utcnow(),
            alert_id
        ))
        
        # Create resolution record (could be separate table in production)
        resolution_data = {
            'resolved_by': user['user_type'],
            'resolver_name': user['full_name'],
            'resolution_notes': resolution_notes,
            'outcome': outcome,
            'resolution_time': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': 'Emergency alert resolved',
            'alert_id': alert_id,
            'resolution': resolution_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Alert resolution failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Alert resolution failed'
        }), 500

@emergency_bp.route('/contacts', methods=['GET'])
def get_emergency_contacts():
    """Get emergency contacts"""
    try:
        contacts = [
            {
                'name': 'Emergency Ambulance',
                'number': '108',
                'description': 'Free 24/7 ambulance service',
                'type': 'ambulance',
                'priority': 1
            },
            {
                'name': 'Police Emergency',
                'number': '100',
                'description': 'Police emergency services',
                'type': 'police',
                'priority': 2
            },
            {
                'name': 'Fire Emergency',
                'number': '101',
                'description': 'Fire and rescue services',
                'type': 'fire',
                'priority': 3
            },
            {
                'name': 'Women Helpline',
                'number': '1091',
                'description': '24x7 helpline for women in distress',
                'type': 'women_safety',
                'priority': 4
            },
            {
                'name': 'Child Helpline',
                'number': '1098',
                'description': 'Emergency helpline for children',
                'type': 'child_safety',
                'priority': 5
            },
            {
                'name': 'Disaster Management',
                'number': '1070',
                'description': 'Natural disaster emergency response',
                'type': 'disaster',
                'priority': 6
            }
        ]
        
        return jsonify({
            'success': True,
            'contacts': contacts,
            'total_count': len(contacts)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Emergency contacts fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch emergency contacts'
        }), 500

@emergency_bp.route('/asha-alerts', methods=['GET'])
@jwt_required()
def get_asha_alerts():
    """Get emergency alerts for ASHA worker"""
    try:
        user_id = get_jwt_identity()
        
        # Get ASHA worker data
        asha = AshaWorker.get_by_user_id(user_id)
        if not asha:
            return jsonify({'error': 'ASHA worker profile not found'}), 404
        
        # Get alerts in assigned villages
        query = """
        SELECT ea.*, c.user_id, u.full_name as citizen_name, u.phone as citizen_phone, u.village
        FROM emergency_alerts ea
        JOIN citizens c ON ea.citizen_id = c.id
        JOIN users u ON c.user_id = u.id
        WHERE u.village = ANY(%s) AND ea.status IN ('active', 'responding')
        ORDER BY ea.created_at DESC
        LIMIT 50
        """
        
        alerts = db.execute_query(query, (asha['assigned_villages'],))
        
        # Format alerts
        formatted_alerts = []
        for alert in alerts:
            formatted_alert = {
                'id': alert['id'],
                'alert_type': alert['alert_type'],
                'severity': alert['severity'],
                'description': alert['description'],
                'location': json.loads(alert['location']) if alert['location'] else {},
                'status': alert['status'],
                'citizen': {
                    'name': alert['citizen_name'],
                    'phone': alert['citizen_phone'],
                    'village': alert['village']
                },
                'response_time': alert['response_time'].isoformat() if alert['response_time'] else None,
                'created_at': alert['created_at'].isoformat(),
                'time_elapsed': str(datetime.utcnow() - alert['created_at'])
            }
            formatted_alerts.append(formatted_alert)
        
        return jsonify({
            'success': True,
            'alerts': formatted_alerts,
            'total_count': len(formatted_alerts),
            'active_alerts': len([a for a in formatted_alerts if a['status'] == 'active']),
            'responding_alerts': len([a for a in formatted_alerts if a['status'] == 'responding'])
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"ASHA alerts fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch ASHA alerts'
        }), 500

def find_nearby_asha_workers(location, citizen):
    """Find nearby ASHA workers"""
    try:
        # Get ASHA workers in the same village/block
        query = """
        SELECT aw.*, u.full_name, u.phone, u.village
        FROM asha_workers aw
        JOIN users u ON aw.user_id = u.id
        WHERE u.village = %s OR %s = ANY(aw.assigned_villages)
        AND u.is_active = true
        ORDER BY aw.performance_score DESC
        LIMIT 5
        """
        
        village = citizen.get('village', '')
        asha_workers = db.execute_query(query, (village, village))
        
        return asha_workers or []
        
    except Exception as e:
        current_app.logger.error(f"Nearby ASHA workers search failed: {str(e)}")
        return []

def send_emergency_notification(asha_worker, alert_id, alert_type, severity):
    """Send emergency notification to ASHA worker"""
    try:
        # Mock notification implementation
        # In production, integrate with SMS/Push notification service
        
        notification_data = {
            'recipient': asha_worker['full_name'],
            'phone': asha_worker.get('phone'),
            'message': f"Emergency Alert: {alert_type} - {severity} severity",
            'alert_id': alert_id,
            'sent_at': datetime.utcnow().isoformat()
        }
        
        # Log notification (in production, send actual notification)
        current_app.logger.info(f"Emergency notification sent: {notification_data}")
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Emergency notification failed: {str(e)}")
        return False

def generate_emergency_response_plan(alert_type, severity, location):
    """Generate emergency response plan"""
    try:
        response_plans = {
            'medical': {
                'high': [
                    'Call 108 ambulance immediately',
                    'Contact nearest ASHA worker',
                    'Prepare patient for transport',
                    'Gather medical history and medications'
                ],
                'medium': [
                    'Contact ASHA worker for assessment',
                    'Monitor vital signs',
                    'Prepare for possible hospital visit',
                    'Keep emergency contacts ready'
                ],
                'low': [
                    'Contact ASHA worker for guidance',
                    'Monitor symptoms',
                    'Follow basic first aid if trained',
                    'Schedule follow-up if needed'
                ]
            },
            'accident': {
                'high': [
                    'Call 108 ambulance immediately',
                    'Do not move injured person unless necessary',
                    'Control bleeding if present',
                    'Keep person conscious and calm'
                ],
                'medium': [
                    'Assess injuries carefully',
                    'Contact ASHA worker',
                    'Apply basic first aid',
                    'Prepare for medical transport'
                ],
                'low': [
                    'Clean and dress minor wounds',
                    'Contact ASHA worker for advice',
                    'Monitor for complications',
                    'Rest and avoid strenuous activity'
                ]
            },
            'breathing': {
                'high': [
                    'Call 108 ambulance immediately',
                    'Keep person upright if conscious',
                    'Loosen tight clothing',
                    'Stay with person until help arrives'
                ],
                'medium': [
                    'Help person sit upright',
                    'Contact ASHA worker immediately',
                    'Ensure fresh air circulation',
                    'Monitor breathing closely'
                ],
                'low': [
                    'Encourage slow, deep breathing',
                    'Contact ASHA worker for guidance',
                    'Remove from any irritants',
                    'Monitor for improvement'
                ]
            },
            'pregnancy': {
                'high': [
                    'Call 108 ambulance immediately',
                    'Contact skilled birth attendant',
                    'Prepare clean delivery area if needed',
                    'Keep mother calm and comfortable'
                ],
                'medium': [
                    'Contact ASHA worker immediately',
                    'Monitor contractions and bleeding',
                    'Prepare for hospital transport',
                    'Keep emergency delivery kit ready'
                ],
                'low': [
                    'Contact ASHA worker for assessment',
                    'Monitor symptoms',
                    'Rest and stay hydrated',
                    'Schedule prenatal check-up'
                ]
            }
        }
        
        plan = response_plans.get(alert_type, {}).get(severity, [
            'Contact ASHA worker immediately',
            'Call 108 if situation worsens',
            'Stay calm and follow basic safety measures'
        ])
        
        return {
            'steps': plan,
            'emergency_number': '108',
            'estimated_response_time': '15-30 minutes',
            'additional_resources': [
                'Nearest hospital location',
                'ASHA worker contact',
                'Emergency medication list'
            ]
        }
        
    except Exception as e:
        current_app.logger.error(f"Response plan generation failed: {str(e)}")
        return {
            'steps': ['Contact emergency services', 'Stay calm', 'Wait for help'],
            'emergency_number': '108'
        }