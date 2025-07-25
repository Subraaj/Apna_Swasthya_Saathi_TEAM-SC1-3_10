#!/usr/bin/env python3
"""
Apna Swasthya Saathi - AI-Powered Rural Healthcare Platform
Main application entry point
"""

import os
import sys
from flask import Flask, jsonify
from app import create_app
from models.user import User

def main():
    """Main application entry point"""
    try:
        # Create Flask application
        app = create_app()
        
        # Create demo users on startup
        with app.app_context():
            User.create_demo_users()
            app.logger.info("Demo users created/verified")
        
        # Get configuration
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV', 'development') == 'development'
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                 Apna Swasthya Saathi API                     ║
║              AI-Powered Rural Healthcare                     ║
╠══════════════════════════════════════════════════════════════╣
║ Status: Starting server...                                   ║
║ Host: {host:<50} ║
║ Port: {port:<50} ║
║ Debug: {debug:<49} ║
║ Environment: {os.environ.get('FLASK_ENV', 'development'):<42} ║
╠══════════════════════════════════════════════════════════════╣
║ API Endpoints:                                               ║
║ • Health Check: GET /health                                  ║
║ • API Info: GET /api/v1/info                                 ║
║ • Authentication: /api/v1/auth/*                             ║
║ • AI Diagnosis: /api/v1/ai/*                                 ║
║ • Government Schemes: /api/v1/schemes/*                      ║
║ • Insurance: /api/v1/insurance/*                             ║
║ • Emergency: /api/v1/emergency/*                             ║
║ • Facilities: /api/v1/facilities/*                           ║
║ • Chat: /api/v1/chat/*                                       ║
║ • Health Records: /api/v1/records/*                          ║
╠══════════════════════════════════════════════════════════════╣
║ Demo Credentials:                                            ║
║ ASHA Worker: asha@demo.com / demo123                         ║
║ Citizen: citizen@demo.com / demo123                          ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        print(f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()