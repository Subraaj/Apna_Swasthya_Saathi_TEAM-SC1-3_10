from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import asyncio
import json
from datetime import datetime
import math

from services.government_api_service import gov_api_service
from models.database import db
from models.user import User

facilities_bp = Blueprint('facilities', __name__)

@facilities_bp.route('/search', methods=['GET'])
@jwt_required()
def search_facilities():
    """Search for healthcare facilities"""
    try:
        user_id = get_jwt_identity()
        
        # Get search parameters
        facility_type = request.args.get('type', 'all')
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        district = request.args.get('district')
        radius_km = request.args.get('radius', 50, type=int)
        bsky_only = request.args.get('bsky_only', 'false').lower() == 'true'
        
        # Get user's location if not provided
        if not latitude or not longitude:
            user = User.find_by_id(user_id)
            district = district or (user['district'] if user else None)
        
        # Prepare location data
        location_data = {
            'latitude': latitude or 0,
            'longitude': longitude or 0,
            'district': district,
            'radius_km': radius_km
        }
        
        # Search facilities
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            facilities_result = loop.run_until_complete(
                gov_api_service.find_nearest_facilities(location_data, facility_type)
            )
        finally:
            loop.close()
        
        if not facilities_result['success']:
            return jsonify({
                'success': False,
                'error': facilities_result['error']
            }), 500
        
        facilities = facilities_result['facilities']
        
        # Filter by BSKY if requested
        if bsky_only:
            facilities = [f for f in facilities if f.get('bsky_empanelled', False)]
        
        # Add additional information
        enhanced_facilities = []
        for facility in facilities:
            enhanced_facility = enhance_facility_data(facility)
            enhanced_facilities.append(enhanced_facility)
        
        return jsonify({
            'success': True,
            'facilities': enhanced_facilities,
            'total_count': len(enhanced_facilities),
            'search_params': {
                'type': facility_type,
                'location': location_data,
                'bsky_only': bsky_only
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Facility search failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Facility search failed'
        }), 500

@facilities_bp.route('/nearby', methods=['GET'])
@jwt_required()
def get_nearby_facilities():
    """Get nearby facilities based on user location"""
    try:
        user_id = get_jwt_identity()
        
        # Get user data
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get facilities in user's district
        query = """
        SELECT * FROM healthcare_facilities 
        WHERE district = %s 
        ORDER BY 
            CASE 
                WHEN bsky_empanelled = true THEN 0 
                ELSE 1 
            END,
            rating DESC,
            name
        LIMIT 20
        """
        
        facilities = db.execute_query(query, (user['district'],))
        
        # Enhance facility data
        enhanced_facilities = []
        for facility in facilities:
            enhanced_facility = enhance_facility_data(facility)
            enhanced_facilities.append(enhanced_facility)
        
        return jsonify({
            'success': True,
            'facilities': enhanced_facilities,
            'user_location': {
                'district': user['district'],
                'block': user['block'],
                'village': user['village']
            },
            'total_count': len(enhanced_facilities)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Nearby facilities fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch nearby facilities'
        }), 500

@facilities_bp.route('/<facility_id>', methods=['GET'])
@jwt_required()
def get_facility_details(facility_id):
    """Get detailed information about a facility"""
    try:
        # Get facility details
        query = "SELECT * FROM healthcare_facilities WHERE id = %s"
        result = db.execute_query(query, (facility_id,))
        
        if not result:
            return jsonify({'error': 'Facility not found'}), 404
        
        facility = result[0]
        
        # Enhance with additional details
        enhanced_facility = enhance_facility_data(facility)
        
        # Add more detailed information
        enhanced_facility.update({
            'detailed_services': get_detailed_services(facility['type']),
            'staff_info': get_staff_info(facility_id),
            'patient_reviews': get_patient_reviews(facility_id),
            'availability_status': get_availability_status(facility_id),
            'insurance_accepted': get_insurance_info(facility_id)
        })
        
        return jsonify({
            'success': True,
            'facility': enhanced_facility
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Facility details fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch facility details'
        }), 500

@facilities_bp.route('/types', methods=['GET'])
def get_facility_types():
    """Get available facility types"""
    try:
        facility_types = [
            {
                'id': 'phc',
                'name': 'Primary Health Center',
                'description': 'Basic healthcare services for rural areas',
                'services': ['General Medicine', 'Maternal Care', 'Vaccination', 'Basic Diagnostics'],
                'typical_staff': ['Medical Officer', 'ANM', 'Pharmacist']
            },
            {
                'id': 'chc',
                'name': 'Community Health Center',
                'description': 'Secondary healthcare with specialist services',
                'services': ['Specialist Consultation', 'Surgery', 'Laboratory', 'X-Ray'],
                'typical_staff': ['Specialists', 'Surgeons', 'Lab Technicians']
            },
            {
                'id': 'hospital',
                'name': 'Government Hospital',
                'description': 'Comprehensive healthcare services',
                'services': ['Emergency Care', 'Surgery', 'ICU', 'Specialist Care'],
                'typical_staff': ['Doctors', 'Nurses', 'Specialists', 'Support Staff']
            },
            {
                'id': 'private',
                'name': 'Private Clinic/Hospital',
                'description': 'Private healthcare facilities',
                'services': ['Varies by facility'],
                'typical_staff': ['Private Practitioners']
            },
            {
                'id': 'dispensary',
                'name': 'Dispensary',
                'description': 'Basic medical care and medicines',
                'services': ['Basic Treatment', 'Medicines', 'First Aid'],
                'typical_staff': ['Pharmacist', 'Compounder']
            }
        ]
        
        return jsonify({
            'success': True,
            'facility_types': facility_types,
            'total_count': len(facility_types)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Facility types fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch facility types'
        }), 500

@facilities_bp.route('/add', methods=['POST'])
@jwt_required()
def add_facility():
    """Add new healthcare facility (ASHA workers can suggest)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'type', 'address', 'district']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Get user data to verify ASHA worker
        user = User.find_by_id(user_id)
        if not user or user['user_type'] != 'asha':
            return jsonify({'error': 'Only ASHA workers can add facilities'}), 403
        
        # Create facility record
        facility_id = str(uuid.uuid4())
        
        coordinates = data.get('coordinates', {})
        contact_info = data.get('contact_info', {})
        services = data.get('services', [])
        operating_hours = data.get('operating_hours', {})
        
        query = """
        INSERT INTO healthcare_facilities (id, name, type, address, district, block,
                                         coordinates, contact_info, services, 
                                         bsky_empanelled, operating_hours, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            facility_id,
            data['name'],
            data['type'],
            data['address'],
            data['district'],
            data.get('block'),
            json.dumps(coordinates),
            json.dumps(contact_info),
            json.dumps(services),
            data.get('bsky_empanelled', False),
            json.dumps(operating_hours),
            datetime.utcnow()
        )
        
        db.execute_query(query, params)
        
        return jsonify({
            'success': True,
            'message': 'Healthcare facility added successfully',
            'facility_id': facility_id,
            'status': 'pending_verification'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Facility addition failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to add facility'
        }), 500

@facilities_bp.route('/directions', methods=['POST'])
@jwt_required()
def get_directions():
    """Get directions to a facility"""
    try:
        data = request.get_json()
        
        facility_id = data.get('facility_id')
        user_location = data.get('user_location', {})
        
        if not facility_id:
            return jsonify({'error': 'Facility ID is required'}), 400
        
        # Get facility location
        query = "SELECT name, address, coordinates FROM healthcare_facilities WHERE id = %s"
        result = db.execute_query(query, (facility_id,))
        
        if not result:
            return jsonify({'error': 'Facility not found'}), 404
        
        facility = result[0]
        facility_coords = json.loads(facility['coordinates']) if facility['coordinates'] else {}
        
        # Calculate distance and generate directions (mock implementation)
        if user_location.get('latitude') and user_location.get('longitude') and facility_coords.get('lat') and facility_coords.get('lng'):
            distance = calculate_distance(
                user_location['latitude'], user_location['longitude'],
                facility_coords['lat'], facility_coords['lng']
            )
        else:
            distance = None
        
        directions = {
            'facility': {
                'name': facility['name'],
                'address': facility['address'],
                'coordinates': facility_coords
            },
            'distance_km': distance,
            'estimated_time': f"{int(distance * 2)} minutes" if distance else "Unknown",
            'directions_url': generate_directions_url(user_location, facility_coords),
            'transport_options': [
                {'mode': 'walking', 'time': f"{int(distance * 12)} minutes" if distance else "Unknown"},
                {'mode': 'auto', 'time': f"{int(distance * 3)} minutes" if distance else "Unknown"},
                {'mode': 'bus', 'time': f"{int(distance * 4)} minutes" if distance else "Unknown"}
            ] if distance else []
        }
        
        return jsonify({
            'success': True,
            'directions': directions
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Directions fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get directions'
        }), 500

@facilities_bp.route('/emergency-nearby', methods=['POST'])
@jwt_required()
def get_emergency_facilities():
    """Get nearby facilities for emergency situations"""
    try:
        data = request.get_json()
        
        emergency_type = data.get('emergency_type', 'general')
        user_location = data.get('user_location', {})
        max_distance = data.get('max_distance_km', 25)
        
        # Get facilities with emergency services
        query = """
        SELECT * FROM healthcare_facilities 
        WHERE (services::text LIKE '%emergency%' OR services::text LIKE '%24/7%' OR type = 'hospital')
        AND coordinates IS NOT NULL
        ORDER BY 
            CASE WHEN bsky_empanelled = true THEN 0 ELSE 1 END,
            rating DESC
        LIMIT 10
        """
        
        facilities = db.execute_query(query)
        
        # Filter by distance if user location provided
        if user_location.get('latitude') and user_location.get('longitude'):
            nearby_facilities = []
            for facility in facilities:
                coords = json.loads(facility['coordinates']) if facility['coordinates'] else {}
                if coords.get('lat') and coords.get('lng'):
                    distance = calculate_distance(
                        user_location['latitude'], user_location['longitude'],
                        coords['lat'], coords['lng']
                    )
                    if distance <= max_distance:
                        facility_data = enhance_facility_data(facility)
                        facility_data['distance_km'] = distance
                        facility_data['estimated_time'] = f"{int(distance * 2)} minutes"
                        nearby_facilities.append(facility_data)
            
            # Sort by distance
            nearby_facilities.sort(key=lambda x: x['distance_km'])
            facilities = nearby_facilities
        else:
            facilities = [enhance_facility_data(f) for f in facilities]
        
        # Add emergency-specific information
        for facility in facilities:
            facility['emergency_services'] = get_emergency_services(facility['type'])
            facility['contact_priority'] = 'high' if facility.get('bsky_empanelled') else 'medium'
        
        return jsonify({
            'success': True,
            'emergency_facilities': facilities,
            'emergency_type': emergency_type,
            'total_count': len(facilities),
            'emergency_contacts': [
                {'name': 'Ambulance', 'number': '108'},
                {'name': 'Police', 'number': '100'},
                {'name': 'Fire', 'number': '101'}
            ]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Emergency facilities fetch failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch emergency facilities'
        }), 500

def enhance_facility_data(facility):
    """Enhance facility data with additional information"""
    try:
        enhanced = dict(facility)
        
        # Parse JSON fields
        if isinstance(enhanced.get('coordinates'), str):
            enhanced['coordinates'] = json.loads(enhanced['coordinates'])
        if isinstance(enhanced.get('contact_info'), str):
            enhanced['contact_info'] = json.loads(enhanced['contact_info'])
        if isinstance(enhanced.get('services'), str):
            enhanced['services'] = json.loads(enhanced['services'])
        if isinstance(enhanced.get('operating_hours'), str):
            enhanced['operating_hours'] = json.loads(enhanced['operating_hours'])
        
        # Add computed fields
        enhanced['is_24x7'] = is_facility_24x7(enhanced.get('operating_hours', {}))
        enhanced['has_emergency'] = has_emergency_services(enhanced.get('services', []))
        enhanced['facility_category'] = get_facility_category(enhanced['type'])
        
        # Format dates
        if enhanced.get('created_at'):
            enhanced['created_at'] = enhanced['created_at'].isoformat()
        
        return enhanced
        
    except Exception as e:
        current_app.logger.error(f"Facility data enhancement failed: {str(e)}")
        return facility

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    try:
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
        
    except Exception:
        return None

def generate_directions_url(user_location, facility_coords):
    """Generate directions URL for maps"""
    try:
        if not user_location.get('latitude') or not facility_coords.get('lat'):
            return None
        
        # Google Maps directions URL
        base_url = "https://www.google.com/maps/dir/"
        origin = f"{user_location['latitude']},{user_location['longitude']}"
        destination = f"{facility_coords['lat']},{facility_coords['lng']}"
        
        return f"{base_url}{origin}/{destination}"
        
    except Exception:
        return None

def get_detailed_services(facility_type):
    """Get detailed services based on facility type"""
    services_map = {
        'phc': [
            'General Medicine',
            'Maternal and Child Health',
            'Immunization',
            'Family Planning',
            'Basic Laboratory Services',
            'Pharmacy',
            'Health Education'
        ],
        'chc': [
            'Specialist Consultation',
            'Minor Surgery',
            'Laboratory Services',
            'X-Ray',
            'Emergency Care',
            'Inpatient Services',
            'Blood Storage'
        ],
        'hospital': [
            'Emergency Services',
            'Inpatient Care',
            'Surgery',
            'ICU',
            'Specialist Consultation',
            'Diagnostic Services',
            'Pharmacy',
            'Blood Bank'
        ]
    }
    
    return services_map.get(facility_type, ['General Healthcare Services'])

def get_staff_info(facility_id):
    """Get staff information (mock data)"""
    return {
        'total_staff': 15,
        'doctors': 3,
        'nurses': 8,
        'support_staff': 4,
        'availability': '24/7 emergency staff available'
    }

def get_patient_reviews(facility_id):
    """Get patient reviews (mock data)"""
    return [
        {
            'rating': 4,
            'comment': 'Good service and caring staff',
            'date': '2024-01-15'
        },
        {
            'rating': 5,
            'comment': 'Quick treatment and clean facility',
            'date': '2024-01-10'
        }
    ]

def get_availability_status(facility_id):
    """Get current availability status"""
    return {
        'status': 'open',
        'current_wait_time': '15 minutes',
        'beds_available': 5,
        'emergency_available': True
    }

def get_insurance_info(facility_id):
    """Get insurance information"""
    return {
        'bsky_accepted': True,
        'pmjay_accepted': True,
        'private_insurance': ['Star Health', 'HDFC Ergo'],
        'cashless_facility': True
    }

def is_facility_24x7(operating_hours):
    """Check if facility operates 24x7"""
    if not operating_hours:
        return False
    
    return operating_hours.get('24x7', False) or operating_hours.get('emergency_24x7', False)

def has_emergency_services(services):
    """Check if facility has emergency services"""
    if not services:
        return False
    
    emergency_keywords = ['emergency', '24/7', 'urgent', 'trauma']
    services_text = ' '.join(services).lower()
    
    return any(keyword in services_text for keyword in emergency_keywords)

def get_facility_category(facility_type):
    """Get facility category"""
    categories = {
        'phc': 'Primary Care',
        'chc': 'Secondary Care',
        'hospital': 'Tertiary Care',
        'private': 'Private Care',
        'dispensary': 'Basic Care'
    }
    
    return categories.get(facility_type, 'Healthcare Facility')

def get_emergency_services(facility_type):
    """Get emergency services available"""
    emergency_services = {
        'hospital': [
            'Emergency Room',
            'Trauma Care',
            'Ambulance Service',
            'ICU',
            'Blood Bank'
        ],
        'chc': [
            'Emergency Care',
            'Basic Trauma',
            'Stabilization',
            'Referral Services'
        ],
        'phc': [
            'First Aid',
            'Basic Emergency Care',
            'Referral to Higher Centers'
        ]
    }
    
    return emergency_services.get(facility_type, ['Basic Emergency Care'])