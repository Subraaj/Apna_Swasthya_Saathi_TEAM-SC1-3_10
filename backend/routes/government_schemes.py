from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import asyncio
import json
from datetime import datetime

from services.government_api_service import gov_api_service
from models.database import db
from models.user import User, Citizen

schemes_bp = Blueprint('schemes', __name__)

@schemes_bp.route('/check-eligibility', methods=['POST'])
@jwt_required()
def check_eligibility():
    """Check eligibility for government schemes"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        scheme_name = data.get('scheme_name', 'BSKY')
        
        # Get user and citizen data
        user = User.find_by_id(user_id)
        citizen = Citizen.get_by_user_id(user_id)
        
        if not user or not citizen:
            return jsonify({'error': 'User profile not found'}), 404
        
        # Prepare citizen data for eligibility check
        citizen_data = {
            'user_id': user_id,
            'full_name': user['full_name'],
            'district': user['district'],
            'block': user['block'],
            'village': user['village'],
            'phone': user['phone'],
            'abha_id': user['abha_id'],
            'date_of_birth': citizen['date_of_birth'].isoformat() if citizen['date_of_birth'] else None,
            'gender': citizen['gender'],
            'blood_group': citizen['blood_group']
        }
        
        # Check eligibility based on scheme
        if scheme_name.upper() == 'BSKY':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                eligibility_result = loop.run_until_complete(
                    gov_api_service.check_bsky_eligibility(citizen_data)
                )
            finally:
                loop.close()
        else:
            eligibility_result = {
                'success': False,
                'error': 'Scheme not supported',
                'message': f'Eligibility check for {scheme_name} is not yet available'
            }
        
        return jsonify({
            'success': eligibility_result['success'],
            'scheme_name': scheme_name,
            'eligibility_data': eligibility_result.get('details', {}),
            'eligible': eligibility_result.get('eligible', False),
            'message': eligibility_result.get('message', ''),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Eligibility check failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Eligibility check failed',
            'message': 'Please contact your ASHA worker for manual verification'
        }), 500

@schemes_bp.route('/bsky/hospitals', methods=['GET'])
@jwt_required()
def get_bsky_hospitals():
    """Get BSKY empanelled hospitals"""
    try:
        user_id = get_jwt_identity()
        district = request.args.get('district')
        
        # Get user's district if not provided
        if not district:
            user = User.find_by_id(user_id)
            district = user['district'] if user else None
        
        if not district:
            return jsonify({'error': 'District information required'}), 400
        
        # Get empanelled hospitals
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            hospitals = loop.run_until_complete(
                gov_api_service._get_empanelled_hospitals(district)
            )
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'district': district,
            'hospitals': hospitals,
            'total_count': len(hospitals)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"BSKY hospitals fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch BSKY hospitals'
        }), 500

@schemes_bp.route('/benefits', methods=['GET'])
@jwt_required()
def get_scheme_benefits():
    """Get scheme benefits for user"""
    try:
        user_id = get_jwt_identity()
        scheme_name = request.args.get('scheme_name', 'BSKY')
        
        # Get scheme benefits
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            benefits_result = loop.run_until_complete(
                gov_api_service.get_scheme_benefits(user_id, scheme_name)
            )
        finally:
            loop.close()
        
        if benefits_result['success']:
            return jsonify({
                'success': True,
                'scheme_benefits': benefits_result['scheme_data']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': benefits_result['error'],
                'message': 'No scheme data found. Please check eligibility first.'
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Scheme benefits fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch scheme benefits'
        }), 500

@schemes_bp.route('/vaccination-centers', methods=['GET'])
@jwt_required()
def get_vaccination_centers():
    """Get vaccination centers"""
    try:
        user_id = get_jwt_identity()
        district = request.args.get('district')
        date = request.args.get('date')
        
        # Get user's district if not provided
        if not district:
            user = User.find_by_id(user_id)
            district = user['district'] if user else None
        
        if not district:
            return jsonify({'error': 'District information required'}), 400
        
        # Get vaccination centers
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            centers_result = loop.run_until_complete(
                gov_api_service.get_vaccination_centers(district, date)
            )
        finally:
            loop.close()
        
        return jsonify({
            'success': centers_result['success'],
            'district': district,
            'date': centers_result.get('date'),
            'centers': centers_result.get('centers', []),
            'total_count': len(centers_result.get('centers', []))
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Vaccination centers fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch vaccination centers'
        }), 500

@schemes_bp.route('/abha/create', methods=['POST'])
@jwt_required()
def create_abha_id():
    """Create ABHA ID for citizen"""
    try:
        user_id = get_jwt_identity()
        
        # Get user data
        user = User.find_by_id(user_id)
        citizen = Citizen.get_by_user_id(user_id)
        
        if not user or not citizen:
            return jsonify({'error': 'User profile not found'}), 404
        
        # Check if ABHA ID already exists
        if user.get('abha_id'):
            return jsonify({
                'success': True,
                'message': 'ABHA ID already exists',
                'abha_id': user['abha_id']
            }), 200
        
        # Prepare citizen data
        citizen_data = {
            'user_id': user_id,
            'full_name': user['full_name'],
            'phone': user['phone'],
            'district': user['district'],
            'date_of_birth': citizen['date_of_birth'].isoformat() if citizen['date_of_birth'] else None,
            'gender': citizen['gender']
        }
        
        # Create ABHA ID
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            abha_result = loop.run_until_complete(
                gov_api_service.create_abha_id(citizen_data)
            )
        finally:
            loop.close()
        
        if abha_result['success']:
            return jsonify({
                'success': True,
                'message': 'ABHA ID created successfully',
                'abha_data': abha_result['abha_data']
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': abha_result['error'],
                'message': 'ABHA ID creation failed'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"ABHA ID creation failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'ABHA ID creation failed'
        }), 500

@schemes_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_for_scheme():
    """Apply for government scheme"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        scheme_name = data.get('scheme_name')
        application_data = data.get('application_data', {})
        
        if not scheme_name:
            return jsonify({'error': 'Scheme name is required'}), 400
        
        # Get citizen ID
        citizen_query = "SELECT id FROM citizens WHERE user_id = %s"
        citizen_result = db.execute_query(citizen_query, (user_id,))
        
        if not citizen_result:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        citizen_id = citizen_result[0]['id']
        
        # Check if application already exists
        existing_query = """
        SELECT id FROM government_schemes 
        WHERE citizen_id = %s AND scheme_name = %s
        """
        existing = db.execute_query(existing_query, (citizen_id, scheme_name))
        
        if existing:
            # Update existing application
            update_query = """
            UPDATE government_schemes 
            SET application_status = %s, documents_submitted = %s, created_at = %s
            WHERE id = %s
            """
            db.execute_query(update_query, (
                'submitted',
                json.dumps(application_data),
                datetime.utcnow(),
                existing[0]['id']
            ))
            
            application_id = existing[0]['id']
        else:
            # Create new application
            application_id = str(uuid.uuid4())
            insert_query = """
            INSERT INTO government_schemes (id, citizen_id, scheme_name, 
                                          application_status, documents_submitted, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            db.execute_query(insert_query, (
                application_id,
                citizen_id,
                scheme_name,
                'submitted',
                json.dumps(application_data),
                datetime.utcnow()
            ))
        
        return jsonify({
            'success': True,
            'message': f'Application for {scheme_name} submitted successfully',
            'application_id': application_id,
            'status': 'submitted',
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Scheme application failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Scheme application failed'
        }), 500

@schemes_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_user_applications():
    """Get user's scheme applications"""
    try:
        user_id = get_jwt_identity()
        
        query = """
        SELECT gs.*, c.user_id
        FROM government_schemes gs
        JOIN citizens c ON gs.citizen_id = c.id
        WHERE c.user_id = %s
        ORDER BY gs.created_at DESC
        """
        
        applications = db.execute_query(query, (user_id,))
        
        formatted_applications = []
        for app in applications:
            formatted_app = {
                'id': app['id'],
                'scheme_name': app['scheme_name'],
                'scheme_id': app['scheme_id'],
                'eligibility_status': app['eligibility_status'],
                'application_status': app['application_status'],
                'benefits_availed': json.loads(app['benefits_availed']) if app['benefits_availed'] else {},
                'documents_submitted': json.loads(app['documents_submitted']) if app['documents_submitted'] else {},
                'approved_amount': float(app['approved_amount']) if app['approved_amount'] else 0.0,
                'created_at': app['created_at'].isoformat(),
                'last_updated': app['created_at'].isoformat()
            }
            formatted_applications.append(formatted_app)
        
        return jsonify({
            'success': True,
            'applications': formatted_applications,
            'total_count': len(formatted_applications)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"User applications fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch applications'
        }), 500

@schemes_bp.route('/schemes-info', methods=['GET'])
def get_schemes_info():
    """Get information about available schemes"""
    try:
        schemes_info = {
            'BSKY': {
                'name': 'Biju Swasthya Kalyan Yojana',
                'description': 'Comprehensive health coverage for all families in Odisha',
                'coverage_amount': 500000,
                'eligibility': 'All families covered under NFSA/SFSS',
                'benefits': [
                    'Cashless treatment at empanelled hospitals',
                    'Pre and post hospitalization coverage',
                    'Day care procedures included',
                    'Women and children get additional benefits'
                ],
                'documents_required': [
                    'Ration Card',
                    'Aadhaar Card',
                    'Income Certificate',
                    'Residence Certificate'
                ],
                'application_process': [
                    'Check eligibility online',
                    'Submit required documents',
                    'Get verification from ASHA worker',
                    'Receive scheme card'
                ]
            },
            'NIRAMAYA': {
                'name': 'NIRAMAYA Scheme',
                'description': 'Free medicines for common ailments',
                'coverage_amount': 0,
                'eligibility': 'All citizens at PHCs and CHCs',
                'benefits': [
                    'Essential medicines available free',
                    'Covers 348 generic medicines',
                    'Available at all government facilities',
                    'No income or category restrictions'
                ],
                'documents_required': [
                    'Valid ID proof',
                    'Prescription from registered doctor'
                ],
                'application_process': [
                    'Visit nearest PHC/CHC',
                    'Get prescription from doctor',
                    'Collect free medicines from pharmacy'
                ]
            },
            'PMJAY': {
                'name': 'Pradhan Mantri Jan Arogya Yojana',
                'description': 'National health protection scheme',
                'coverage_amount': 500000,
                'eligibility': 'Families identified in SECC database',
                'benefits': [
                    'Cashless treatment',
                    'Secondary and tertiary care',
                    'Pre-existing conditions covered',
                    'No cap on family size'
                ],
                'documents_required': [
                    'PMJAY Card',
                    'Aadhaar Card',
                    'Family ID'
                ],
                'application_process': [
                    'Check eligibility at CSC',
                    'Generate e-card',
                    'Visit empanelled hospital',
                    'Get cashless treatment'
                ]
            }
        }
        
        return jsonify({
            'success': True,
            'schemes': schemes_info,
            'total_schemes': len(schemes_info)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Schemes info fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch schemes information'
        }), 500