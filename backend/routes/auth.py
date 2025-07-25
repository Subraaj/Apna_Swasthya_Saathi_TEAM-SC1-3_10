from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

from models.user import User, AshaWorker, Citizen
from models.database import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'user_type', 'full_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        existing_user = User.find_by_email(data['email'])
        if existing_user:
            return jsonify({'error': 'User already exists'}), 409
        
        # Create new user
        user = User(
            email=data['email'],
            password=data['password'],
            user_type=data['user_type'],
            full_name=data['full_name'],
            phone=data.get('phone'),
            abha_id=data.get('abha_id'),
            district=data.get('district'),
            block=data.get('block'),
            village=data.get('village')
        )
        
        # Save user
        user.save()
        
        # Create user profile based on type
        if data['user_type'] == 'asha':
            asha_query = """
            INSERT INTO asha_workers (user_id, asha_id, certification_number, 
                                    assigned_villages, training_status)
            VALUES (%s, %s, %s, %s, %s)
            """
            db.execute_query(asha_query, (
                user.id,
                data.get('asha_id', f'ASHA{user.id[-6:]}'),
                data.get('certification_number'),
                data.get('assigned_villages', []),
                'pending'
            ))
        elif data['user_type'] == 'citizen':
            citizen_query = """
            INSERT INTO citizens (user_id, date_of_birth, gender, blood_group, 
                                emergency_contact)
            VALUES (%s, %s, %s, %s, %s)
            """
            db.execute_query(citizen_query, (
                user.id,
                data.get('date_of_birth'),
                data.get('gender'),
                data.get('blood_group'),
                data.get('emergency_contact')
            ))
        
        # Generate tokens
        access_token, refresh_token = User.generate_tokens(user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'user_type': user.user_type,
                'full_name': user.full_name
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Registration failed: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.find_by_email(data['email'])
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not User.verify_password(user['password_hash'], data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate tokens
        access_token, refresh_token = User.generate_tokens(user['id'])
        
        # Get user profile data
        profile_data = {}
        if user['user_type'] == 'asha':
            asha_data = AshaWorker.get_by_user_id(user['id'])
            profile_data = asha_data if asha_data else {}
        elif user['user_type'] == 'citizen':
            citizen_data = Citizen.get_by_user_id(user['id'])
            profile_data = citizen_data if citizen_data else {}
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'user_type': user['user_type'],
                'full_name': user['full_name'],
                'phone': user['phone'],
                'abha_id': user['abha_id'],
                'district': user['district'],
                'profile': profile_data
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login failed: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/demo-login', methods=['POST'])
def demo_login():
    """Demo login for testing"""
    try:
        data = request.get_json()
        user_type = data.get('user_type', 'citizen')
        
        # Get demo credentials
        if user_type == 'asha':
            email = current_app.config['DEMO_ASHA_EMAIL']
            password = current_app.config['DEMO_ASHA_PASSWORD']
        else:
            email = current_app.config['DEMO_CITIZEN_EMAIL']
            password = current_app.config['DEMO_CITIZEN_PASSWORD']
        
        # Find user
        user = User.find_by_email(email)
        if not user:
            # Create demo users if they don't exist
            User.create_demo_users()
            user = User.find_by_email(email)
        
        if not user:
            return jsonify({'error': 'Demo user not found'}), 404
        
        # Generate tokens
        access_token, refresh_token = User.generate_tokens(user['id'])
        
        # Get profile data
        profile_data = {}
        if user['user_type'] == 'asha':
            asha_data = AshaWorker.get_by_user_id(user['id'])
            profile_data = asha_data if asha_data else {}
        elif user['user_type'] == 'citizen':
            citizen_data = Citizen.get_by_user_id(user['id'])
            profile_data = citizen_data if citizen_data else {}
        
        return jsonify({
            'message': 'Demo login successful',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'user_type': user['user_type'],
                'full_name': user['full_name'],
                'phone': user['phone'],
                'abha_id': user['abha_id'],
                'district': user['district'],
                'profile': profile_data
            },
            'access_token': access_token,
            'refresh_token': refresh_token,
            'demo_credentials': {
                'email': email,
                'password': password
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Demo login failed: {str(e)}")
        return jsonify({'error': 'Demo login failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get profile data based on user type
        profile_data = {}
        if user['user_type'] == 'asha':
            asha_data = AshaWorker.get_by_user_id(user_id)
            profile_data = asha_data if asha_data else {}
        elif user['user_type'] == 'citizen':
            citizen_data = Citizen.get_by_user_id(user_id)
            profile_data = citizen_data if citizen_data else {}
        
        return jsonify({
            'user': {
                'id': user['id'],
                'email': user['email'],
                'user_type': user['user_type'],
                'full_name': user['full_name'],
                'phone': user['phone'],
                'abha_id': user['abha_id'],
                'district': user['district'],
                'block': user['block'],
                'village': user['village'],
                'profile': profile_data
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Profile fetch failed: {str(e)}")
        return jsonify({'error': 'Profile fetch failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        user_id = get_jwt_identity()
        new_token = create_access_token(identity=user_id)
        
        return jsonify({
            'access_token': new_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh failed: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout"""
    try:
        # In a production system, you would blacklist the token
        # For now, we'll just return success
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout failed: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500