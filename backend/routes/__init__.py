from flask import Blueprint
from routes.auth import auth_bp
from routes.ai_diagnosis import ai_bp
from routes.government_schemes import schemes_bp
from routes.insurance import insurance_bp
from routes.emergency import emergency_bp
from routes.facilities import facilities_bp
from routes.chat import chat_bp
from routes.health_records import records_bp

def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    
    # API version prefix
    api_prefix = '/api/v1'
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix=f'{api_prefix}/auth')
    app.register_blueprint(ai_bp, url_prefix=f'{api_prefix}/ai')
    app.register_blueprint(schemes_bp, url_prefix=f'{api_prefix}/schemes')
    app.register_blueprint(insurance_bp, url_prefix=f'{api_prefix}/insurance')
    app.register_blueprint(emergency_bp, url_prefix=f'{api_prefix}/emergency')
    app.register_blueprint(facilities_bp, url_prefix=f'{api_prefix}/facilities')
    app.register_blueprint(chat_bp, url_prefix=f'{api_prefix}/chat')
    app.register_blueprint(records_bp, url_prefix=f'{api_prefix}/records')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'Apna Swasthya Saathi API'}, 200
    
    # API info endpoint
    @app.route(f'{api_prefix}/info')
    def api_info():
        return {
            'service': 'Apna Swasthya Saathi',
            'version': '1.0.0',
            'description': 'AI-powered rural healthcare platform',
            'endpoints': {
                'auth': f'{api_prefix}/auth',
                'ai_diagnosis': f'{api_prefix}/ai',
                'government_schemes': f'{api_prefix}/schemes',
                'insurance': f'{api_prefix}/insurance',
                'emergency': f'{api_prefix}/emergency',
                'facilities': f'{api_prefix}/facilities',
                'chat': f'{api_prefix}/chat',
                'health_records': f'{api_prefix}/records'
            }
        }, 200