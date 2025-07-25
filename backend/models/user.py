from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import datetime
import uuid
from models.database import db

class User:
    def __init__(self, email, password, user_type, full_name, **kwargs):
        self.id = str(uuid.uuid4())
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.user_type = user_type
        self.full_name = full_name
        self.phone = kwargs.get('phone')
        self.abha_id = kwargs.get('abha_id')
        self.district = kwargs.get('district')
        self.block = kwargs.get('block')
        self.village = kwargs.get('village')
        self.is_active = True
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def save(self):
        """Save user to database"""
        query = """
        INSERT INTO users (id, email, password_hash, user_type, full_name, phone, 
                          abha_id, district, block, village, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            self.id, self.email, self.password_hash, self.user_type, self.full_name,
            self.phone, self.abha_id, self.district, self.block, self.village,
            self.is_active, self.created_at, self.updated_at
        )
        
        return db.execute_query(query, params)
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        query = "SELECT * FROM users WHERE email = %s AND is_active = true"
        result = db.execute_query(query, (email,))
        return result[0] if result else None
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        query = "SELECT * FROM users WHERE id = %s AND is_active = true"
        result = db.execute_query(query, (user_id,))
        return result[0] if result else None
    
    @staticmethod
    def verify_password(password_hash, password):
        """Verify password"""
        return check_password_hash(password_hash, password)
    
    @staticmethod
    def generate_tokens(user_id):
        """Generate JWT tokens"""
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)
        return access_token, refresh_token
    
    @staticmethod
    def create_demo_users():
        """Create demo users for testing"""
        from config.config import Config
        
        # Demo ASHA worker
        asha_user = User(
            email=Config.DEMO_ASHA_EMAIL,
            password=Config.DEMO_ASHA_PASSWORD,
            user_type='asha',
            full_name='Priya Patel',
            phone='+91 9876543210',
            district='Koraput',
            block='Koraput',
            village='Kendrapara'
        )
        
        # Demo Citizen
        citizen_user = User(
            email=Config.DEMO_CITIZEN_EMAIL,
            password=Config.DEMO_CITIZEN_PASSWORD,
            user_type='citizen',
            full_name='Ramesh Kumar',
            phone='+91 9876543211',
            abha_id='12-3456-7890-1234',
            district='Koraput',
            block='Koraput',
            village='Bhadrak'
        )
        
        try:
            # Check if demo users already exist
            existing_asha = User.find_by_email(Config.DEMO_ASHA_EMAIL)
            existing_citizen = User.find_by_email(Config.DEMO_CITIZEN_EMAIL)
            
            if not existing_asha:
                asha_user.save()
                # Create ASHA worker profile
                asha_query = """
                INSERT INTO asha_workers (user_id, asha_id, certification_number, 
                                        assigned_villages, training_status, performance_score)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                db.execute_query(asha_query, (
                    asha_user.id, 'ASHA001', 'CERT2024001',
                    ['Kendrapara', 'Bhadrak'], 'completed', 4.8
                ))
            
            if not existing_citizen:
                citizen_user.save()
                # Create citizen profile
                citizen_query = """
                INSERT INTO citizens (user_id, date_of_birth, gender, blood_group, 
                                    emergency_contact, medical_history)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                db.execute_query(citizen_query, (
                    citizen_user.id, '1985-05-15', 'Male', 'B+',
                    '+91 9876543212', '{"conditions": ["hypertension"], "allergies": []}'
                ))
            
            return True
            
        except Exception as e:
            print(f"Error creating demo users: {str(e)}")
            return False

class AshaWorker:
    @staticmethod
    def get_by_user_id(user_id):
        """Get ASHA worker by user ID"""
        query = """
        SELECT aw.*, u.full_name, u.email, u.phone, u.district, u.block, u.village
        FROM asha_workers aw
        JOIN users u ON aw.user_id = u.id
        WHERE aw.user_id = %s
        """
        result = db.execute_query(query, (user_id,))
        return result[0] if result else None
    
    @staticmethod
    def get_patients(asha_user_id):
        """Get patients assigned to ASHA worker"""
        query = """
        SELECT c.*, u.full_name, u.email, u.phone, u.village,
               hr.risk_level, hr.created_at as last_visit
        FROM citizens c
        JOIN users u ON c.user_id = u.id
        LEFT JOIN health_records hr ON c.id = hr.citizen_id
        WHERE u.village = ANY(
            SELECT unnest(assigned_villages) 
            FROM asha_workers 
            WHERE user_id = %s
        )
        ORDER BY hr.created_at DESC
        """
        return db.execute_query(query, (asha_user_id,))

class Citizen:
    @staticmethod
    def get_by_user_id(user_id):
        """Get citizen by user ID"""
        query = """
        SELECT c.*, u.full_name, u.email, u.phone, u.abha_id, u.district, u.block, u.village
        FROM citizens c
        JOIN users u ON c.user_id = u.id
        WHERE c.user_id = %s
        """
        result = db.execute_query(query, (user_id,))
        return result[0] if result else None