from supabase import create_client, Client
from flask import current_app
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

class Database:
    def __init__(self):
        self.supabase: Client = None
        self.pg_conn = None
    
    def init_app(self, app):
        """Initialize database connections"""
        try:
            # Initialize Supabase client
            self.supabase = create_client(
                app.config['SUPABASE_URL'],
                app.config['SUPABASE_KEY']
            )
            
            # Initialize PostgreSQL connection (backup)
            self.pg_conn = psycopg2.connect(
                app.config['SQLALCHEMY_DATABASE_URI'],
                cursor_factory=RealDictCursor
            )
            
            app.logger.info("Database connections initialized successfully")
            
        except Exception as e:
            app.logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def get_supabase(self) -> Client:
        """Get Supabase client"""
        return self.supabase
    
    def get_pg_connection(self):
        """Get PostgreSQL connection"""
        return self.pg_conn
    
    def execute_query(self, query, params=None):
        """Execute raw SQL query"""
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    self.pg_conn.commit()
                    return cursor.rowcount
        except Exception as e:
            self.pg_conn.rollback()
            current_app.logger.error(f"Query execution failed: {str(e)}")
            raise

# Global database instance
db = Database()

def init_db(app):
    """Initialize database with app"""
    db.init_app(app)
    
    # Create tables if they don't exist
    create_tables()

def create_tables():
    """Create database tables"""
    tables = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            user_type VARCHAR(50) NOT NULL CHECK (user_type IN ('asha', 'citizen', 'admin')),
            full_name VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            abha_id VARCHAR(50) UNIQUE,
            district VARCHAR(100),
            block VARCHAR(100),
            village VARCHAR(100),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS asha_workers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            asha_id VARCHAR(50) UNIQUE NOT NULL,
            certification_number VARCHAR(100),
            assigned_villages TEXT[],
            supervisor_contact VARCHAR(20),
            training_status VARCHAR(50) DEFAULT 'pending',
            performance_score DECIMAL(3,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS citizens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            date_of_birth DATE,
            gender VARCHAR(10),
            blood_group VARCHAR(5),
            emergency_contact VARCHAR(20),
            medical_history JSONB,
            insurance_details JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS health_records (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS ai_diagnoses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            health_record_id UUID REFERENCES health_records(id) ON DELETE CASCADE,
            model_used VARCHAR(100),
            input_data JSONB,
            prediction_results JSONB,
            confidence_score DECIMAL(5,4),
            processing_time_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS government_schemes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            citizen_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
            scheme_name VARCHAR(100) NOT NULL,
            scheme_id VARCHAR(50),
            eligibility_status VARCHAR(20),
            application_status VARCHAR(20),
            benefits_availed JSONB,
            documents_submitted JSONB,
            approved_amount DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS insurance_policies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            citizen_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
            policy_type VARCHAR(50),
            policy_number VARCHAR(100) UNIQUE,
            premium_amount DECIMAL(10,2),
            coverage_amount DECIMAL(10,2),
            start_date DATE,
            end_date DATE,
            status VARCHAR(20) DEFAULT 'active',
            claims JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS emergency_alerts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            citizen_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            location JSONB,
            description TEXT,
            status VARCHAR(20) DEFAULT 'active',
            responder_id UUID REFERENCES asha_workers(id),
            response_time TIMESTAMP,
            resolution_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS healthcare_facilities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            session_data JSONB,
            language VARCHAR(10) DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]
    
    try:
        for table_sql in tables:
            db.execute_query(table_sql)
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_users_abha_id ON users(abha_id);",
            "CREATE INDEX IF NOT EXISTS idx_health_records_citizen ON health_records(citizen_id);",
            "CREATE INDEX IF NOT EXISTS idx_health_records_date ON health_records(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_emergency_alerts_status ON emergency_alerts(status);",
            "CREATE INDEX IF NOT EXISTS idx_facilities_location ON healthcare_facilities USING GIN(coordinates);"
        ]
        
        for index_sql in indexes:
            db.execute_query(index_sql)
            
        current_app.logger.info("Database tables created successfully")
        
    except Exception as e:
        current_app.logger.error(f"Table creation failed: {str(e)}")
        raise