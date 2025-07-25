from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from models.database import db
from models.user import User, Citizen

insurance_bp = Blueprint('insurance', __name__)

@insurance_bp.route('/products', methods=['GET'])
def get_insurance_products():
    """Get available insurance products"""
    try:
        products = [
            {
                'id': 'basic_health',
                'name': 'Basic Health Cover',
                'description': 'Essential health coverage for individuals and families',
                'premium_monthly': 50,
                'coverage_amount': 5000,
                'features': [
                    'Hospitalization coverage',
                    'Day care procedures',
                    'Ambulance charges',
                    'Pre-hospitalization expenses'
                ],
                'eligibility': {
                    'min_age': 18,
                    'max_age': 65,
                    'family_size': 1
                },
                'popular': True
            },
            {
                'id': 'family_protection',
                'name': 'Family Protection Plan',
                'description': 'Comprehensive coverage for entire family',
                'premium_monthly': 120,
                'coverage_amount': 15000,
                'features': [
                    'Family coverage (up to 4 members)',
                    'Maternity benefits',
                    'Child care coverage',
                    'Pre-existing conditions after waiting period'
                ],
                'eligibility': {
                    'min_age': 18,
                    'max_age': 65,
                    'family_size': 4
                },
                'popular': False
            },
            {
                'id': 'critical_care',
                'name': 'Critical Care Insurance',
                'description': 'Coverage for critical illnesses and major surgeries',
                'premium_monthly': 200,
                'coverage_amount': 25000,
                'features': [
                    'Critical illness cover',
                    'Cancer treatment',
                    'Heart surgery coverage',
                    'Organ transplant coverage'
                ],
                'eligibility': {
                    'min_age': 21,
                    'max_age': 60,
                    'family_size': 1
                },
                'popular': False
            },
            {
                'id': 'women_child',
                'name': 'Women & Child Care',
                'description': 'Specialized coverage for women and children',
                'premium_monthly': 80,
                'coverage_amount': 10000,
                'features': [
                    'Maternity coverage',
                    'Child vaccination',
                    'Women-specific health issues',
                    'Newborn coverage'
                ],
                'eligibility': {
                    'min_age': 18,
                    'max_age': 45,
                    'family_size': 3
                },
                'popular': True
            }
        ]
        
        return jsonify({
            'success': True,
            'products': products,
            'total_count': len(products)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Insurance products fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch insurance products'
        }), 500

@insurance_bp.route('/enroll', methods=['POST'])
@jwt_required()
def enroll_insurance():
    """Enroll in insurance policy"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['product_id', 'coverage_period_months']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        product_id = data['product_id']
        coverage_period = int(data['coverage_period_months'])
        family_members = data.get('family_members', [])
        
        # Get citizen data
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Get product details
        products = get_insurance_products_data()
        product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            return jsonify({'error': 'Invalid product ID'}), 400
        
        # Calculate premium and coverage
        monthly_premium = product['premium_monthly']
        total_premium = monthly_premium * coverage_period
        coverage_amount = product['coverage_amount']
        
        # Create policy
        policy_id = str(uuid.uuid4())
        policy_number = f"ASS{datetime.now().strftime('%Y%m%d')}{policy_id[-6:].upper()}"
        
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=coverage_period * 30)
        
        # Insert policy record
        query = """
        INSERT INTO insurance_policies (id, citizen_id, policy_type, policy_number, 
                                      premium_amount, coverage_amount, start_date, 
                                      end_date, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            policy_id,
            citizen['id'],
            product_id,
            policy_number,
            Decimal(str(total_premium)),
            Decimal(str(coverage_amount)),
            start_date,
            end_date,
            'active',
            datetime.utcnow()
        )
        
        db.execute_query(query, params)
        
        # Create enrollment record with family members
        enrollment_data = {
            'product_details': product,
            'family_members': family_members,
            'enrollment_date': datetime.utcnow().isoformat(),
            'payment_status': 'pending'
        }
        
        return jsonify({
            'success': True,
            'message': 'Insurance enrollment successful',
            'policy': {
                'policy_id': policy_id,
                'policy_number': policy_number,
                'product_name': product['name'],
                'premium_amount': total_premium,
                'coverage_amount': coverage_amount,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'status': 'active'
            },
            'next_steps': [
                'Complete payment process',
                'Download policy document',
                'Share policy details with family'
            ]
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Insurance enrollment failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Insurance enrollment failed'
        }), 500

@insurance_bp.route('/policies', methods=['GET'])
@jwt_required()
def get_user_policies():
    """Get user's insurance policies"""
    try:
        user_id = get_jwt_identity()
        
        # Get citizen ID
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Get policies
        query = """
        SELECT * FROM insurance_policies 
        WHERE citizen_id = %s 
        ORDER BY created_at DESC
        """
        
        policies = db.execute_query(query, (citizen['id'],))
        
        # Format policies
        formatted_policies = []
        products_data = get_insurance_products_data()
        
        for policy in policies:
            # Get product details
            product = next((p for p in products_data if p['id'] == policy['policy_type']), {})
            
            # Calculate days remaining
            days_remaining = (policy['end_date'] - datetime.now().date()).days
            
            formatted_policy = {
                'id': policy['id'],
                'policy_number': policy['policy_number'],
                'policy_type': policy['policy_type'],
                'product_name': product.get('name', 'Unknown Product'),
                'premium_amount': float(policy['premium_amount']),
                'coverage_amount': float(policy['coverage_amount']),
                'start_date': policy['start_date'].isoformat(),
                'end_date': policy['end_date'].isoformat(),
                'status': policy['status'],
                'days_remaining': max(0, days_remaining),
                'claims': json.loads(policy['claims']) if policy['claims'] else [],
                'created_at': policy['created_at'].isoformat()
            }
            
            formatted_policies.append(formatted_policy)
        
        return jsonify({
            'success': True,
            'policies': formatted_policies,
            'total_count': len(formatted_policies),
            'active_policies': len([p for p in formatted_policies if p['status'] == 'active'])
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"User policies fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch insurance policies'
        }), 500

@insurance_bp.route('/claim', methods=['POST'])
@jwt_required()
def file_insurance_claim():
    """File insurance claim"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['policy_id', 'claim_type', 'claim_amount', 'incident_description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        policy_id = data['policy_id']
        claim_type = data['claim_type']
        claim_amount = float(data['claim_amount'])
        incident_description = data['incident_description']
        incident_date = data.get('incident_date', datetime.now().date().isoformat())
        documents = data.get('documents', [])
        
        # Get citizen ID
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Verify policy ownership
        policy_query = """
        SELECT * FROM insurance_policies 
        WHERE id = %s AND citizen_id = %s AND status = 'active'
        """
        
        policy_result = db.execute_query(policy_query, (policy_id, citizen['id']))
        
        if not policy_result:
            return jsonify({'error': 'Policy not found or inactive'}), 404
        
        policy = policy_result[0]
        
        # Check if claim amount is within coverage
        if claim_amount > float(policy['coverage_amount']):
            return jsonify({
                'error': 'Claim amount exceeds coverage limit',
                'coverage_amount': float(policy['coverage_amount'])
            }), 400
        
        # Create claim
        claim_id = str(uuid.uuid4())
        claim_number = f"CLM{datetime.now().strftime('%Y%m%d')}{claim_id[-6:].upper()}"
        
        claim_data = {
            'claim_id': claim_id,
            'claim_number': claim_number,
            'claim_type': claim_type,
            'claim_amount': claim_amount,
            'incident_description': incident_description,
            'incident_date': incident_date,
            'documents': documents,
            'status': 'submitted',
            'submitted_date': datetime.utcnow().isoformat(),
            'estimated_processing_days': 7
        }
        
        # Update policy with claim
        existing_claims = json.loads(policy['claims']) if policy['claims'] else []
        existing_claims.append(claim_data)
        
        update_query = "UPDATE insurance_policies SET claims = %s WHERE id = %s"
        db.execute_query(update_query, (json.dumps(existing_claims), policy_id))
        
        return jsonify({
            'success': True,
            'message': 'Insurance claim filed successfully',
            'claim': {
                'claim_id': claim_id,
                'claim_number': claim_number,
                'status': 'submitted',
                'claim_amount': claim_amount,
                'estimated_processing_days': 7
            },
            'next_steps': [
                'Upload required documents',
                'Track claim status',
                'Contact support if needed'
            ]
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Insurance claim filing failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Insurance claim filing failed'
        }), 500

@insurance_bp.route('/claims/<policy_id>', methods=['GET'])
@jwt_required()
def get_policy_claims(policy_id):
    """Get claims for a specific policy"""
    try:
        user_id = get_jwt_identity()
        
        # Get citizen ID
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Get policy with claims
        query = """
        SELECT claims FROM insurance_policies 
        WHERE id = %s AND citizen_id = %s
        """
        
        result = db.execute_query(query, (policy_id, citizen['id']))
        
        if not result:
            return jsonify({'error': 'Policy not found'}), 404
        
        claims = json.loads(result[0]['claims']) if result[0]['claims'] else []
        
        return jsonify({
            'success': True,
            'policy_id': policy_id,
            'claims': claims,
            'total_claims': len(claims),
            'pending_claims': len([c for c in claims if c['status'] in ['submitted', 'under_review']])
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Policy claims fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch policy claims'
        }), 500

@insurance_bp.route('/premium-calculator', methods=['POST'])
def calculate_premium():
    """Calculate insurance premium"""
    try:
        data = request.get_json()
        
        product_id = data.get('product_id')
        age = int(data.get('age', 25))
        family_size = int(data.get('family_size', 1))
        coverage_period = int(data.get('coverage_period_months', 12))
        pre_existing_conditions = data.get('pre_existing_conditions', [])
        
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400
        
        # Get product details
        products = get_insurance_products_data()
        product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            return jsonify({'error': 'Invalid product ID'}), 400
        
        # Base premium
        base_premium = product['premium_monthly']
        
        # Age factor
        age_factor = 1.0
        if age > 45:
            age_factor = 1.2
        elif age > 35:
            age_factor = 1.1
        
        # Family size factor
        family_factor = 1.0
        if family_size > 1:
            family_factor = 0.9 + (family_size * 0.15)  # Discount for family plans
        
        # Pre-existing conditions factor
        conditions_factor = 1.0
        if pre_existing_conditions:
            conditions_factor = 1.3
        
        # Calculate final premium
        monthly_premium = base_premium * age_factor * family_factor * conditions_factor
        total_premium = monthly_premium * coverage_period
        
        # Discount for longer terms
        if coverage_period >= 12:
            total_premium *= 0.9  # 10% discount for annual plans
        
        return jsonify({
            'success': True,
            'calculation': {
                'product_id': product_id,
                'product_name': product['name'],
                'base_premium': base_premium,
                'monthly_premium': round(monthly_premium, 2),
                'total_premium': round(total_premium, 2),
                'coverage_amount': product['coverage_amount'],
                'coverage_period_months': coverage_period,
                'factors': {
                    'age_factor': age_factor,
                    'family_factor': family_factor,
                    'conditions_factor': conditions_factor
                },
                'savings': round((base_premium * coverage_period) - total_premium, 2) if total_premium < (base_premium * coverage_period) else 0
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Premium calculation failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Premium calculation failed'
        }), 500

@insurance_bp.route('/renew/<policy_id>', methods=['POST'])
@jwt_required()
def renew_policy(policy_id):
    """Renew insurance policy"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        renewal_period = int(data.get('renewal_period_months', 12))
        
        # Get citizen ID
        citizen = Citizen.get_by_user_id(user_id)
        if not citizen:
            return jsonify({'error': 'Citizen profile not found'}), 404
        
        # Get existing policy
        query = """
        SELECT * FROM insurance_policies 
        WHERE id = %s AND citizen_id = %s
        """
        
        result = db.execute_query(query, (policy_id, citizen['id']))
        
        if not result:
            return jsonify({'error': 'Policy not found'}), 404
        
        old_policy = result[0]
        
        # Get product details for premium calculation
        products = get_insurance_products_data()
        product = next((p for p in products if p['id'] == old_policy['policy_type']), None)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Calculate renewal premium (with loyalty discount)
        base_premium = product['premium_monthly']
        loyalty_discount = 0.05  # 5% loyalty discount
        renewal_premium = base_premium * renewal_period * (1 - loyalty_discount)
        
        # Create new policy for renewal
        new_policy_id = str(uuid.uuid4())
        new_policy_number = f"ASS{datetime.now().strftime('%Y%m%d')}{new_policy_id[-6:].upper()}"
        
        new_start_date = old_policy['end_date']
        new_end_date = new_start_date + timedelta(days=renewal_period * 30)
        
        # Insert renewed policy
        insert_query = """
        INSERT INTO insurance_policies (id, citizen_id, policy_type, policy_number, 
                                      premium_amount, coverage_amount, start_date, 
                                      end_date, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            new_policy_id,
            citizen['id'],
            old_policy['policy_type'],
            new_policy_number,
            Decimal(str(renewal_premium)),
            old_policy['coverage_amount'],
            new_start_date,
            new_end_date,
            'active',
            datetime.utcnow()
        )
        
        db.execute_query(insert_query, params)
        
        # Update old policy status
        update_query = "UPDATE insurance_policies SET status = 'renewed' WHERE id = %s"
        db.execute_query(update_query, (policy_id,))
        
        return jsonify({
            'success': True,
            'message': 'Policy renewed successfully',
            'renewed_policy': {
                'policy_id': new_policy_id,
                'policy_number': new_policy_number,
                'premium_amount': float(renewal_premium),
                'coverage_amount': float(old_policy['coverage_amount']),
                'start_date': new_start_date.isoformat(),
                'end_date': new_end_date.isoformat(),
                'loyalty_discount': loyalty_discount * 100,
                'savings': float(base_premium * renewal_period - renewal_premium)
            }
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Policy renewal failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Policy renewal failed'
        }), 500

def get_insurance_products_data():
    """Get insurance products data (helper function)"""
    return [
        {
            'id': 'basic_health',
            'name': 'Basic Health Cover',
            'premium_monthly': 50,
            'coverage_amount': 5000
        },
        {
            'id': 'family_protection',
            'name': 'Family Protection Plan',
            'premium_monthly': 120,
            'coverage_amount': 15000
        },
        {
            'id': 'critical_care',
            'name': 'Critical Care Insurance',
            'premium_monthly': 200,
            'coverage_amount': 25000
        },
        {
            'id': 'women_child',
            'name': 'Women & Child Care',
            'premium_monthly': 80,
            'coverage_amount': 10000
        }
    ]