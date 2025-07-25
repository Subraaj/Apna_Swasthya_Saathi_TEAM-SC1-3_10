import requests
import json
from datetime import datetime
import logging
from flask import current_app
from models.database import db

class GovernmentAPIService:
    def __init__(self):
        self.bsky_api_url = None
        self.abdm_api_url = None
        self.cowin_api_url = None
        self._initialize_apis()
    
    def _initialize_apis(self):
        """Initialize government API configurations"""
        try:
            self.bsky_api_url = current_app.config.get('BSKY_API_URL')
            self.abdm_api_url = current_app.config.get('ABDM_API_URL')
            self.cowin_api_url = current_app.config.get('COWIN_API_URL')
            
            current_app.logger.info("Government APIs initialized")
            
        except Exception as e:
            current_app.logger.error(f"Government API initialization failed: {str(e)}")
    
    async def check_bsky_eligibility(self, citizen_data):
        """Check BSKY eligibility for citizen"""
        try:
            # Mock BSKY API call (replace with actual API when available)
            eligibility_data = {
                "eligible": True,
                "scheme_id": "BSKY2024",
                "coverage_amount": 500000,
                "family_members_covered": 4,
                "validity": "2024-12-31",
                "empanelled_hospitals": await self._get_empanelled_hospitals(citizen_data.get("district"))
            }
            
            # Save eligibility data
            await self._save_scheme_eligibility(citizen_data.get("user_id"), "BSKY", eligibility_data)
            
            return {
                "success": True,
                "eligible": eligibility_data["eligible"],
                "details": eligibility_data
            }
            
        except Exception as e:
            current_app.logger.error(f"BSKY eligibility check failed: {str(e)}")
            return {
                "success": False,
                "error": "Eligibility check failed",
                "message": "Please contact your ASHA worker for manual verification"
            }
    
    async def _get_empanelled_hospitals(self, district):
        """Get BSKY empanelled hospitals in district"""
        try:
            query = """
            SELECT name, address, contact_info, services
            FROM healthcare_facilities
            WHERE district = %s AND bsky_empanelled = true
            ORDER BY name
            """
            
            hospitals = db.execute_query(query, (district,))
            return hospitals or []
            
        except Exception as e:
            current_app.logger.error(f"Empanelled hospitals fetch failed: {str(e)}")
            return []
    
    async def _save_scheme_eligibility(self, user_id, scheme_name, eligibility_data):
        """Save scheme eligibility data"""
        try:
            # Get citizen ID
            citizen_query = "SELECT id FROM citizens WHERE user_id = %s"
            citizen_result = db.execute_query(citizen_query, (user_id,))
            
            if not citizen_result:
                return False
            
            citizen_id = citizen_result[0]["id"]
            
            # Check if record exists
            existing_query = """
            SELECT id FROM government_schemes 
            WHERE citizen_id = %s AND scheme_name = %s
            """
            existing = db.execute_query(existing_query, (citizen_id, scheme_name))
            
            if existing:
                # Update existing record
                update_query = """
                UPDATE government_schemes 
                SET eligibility_status = %s, benefits_availed = %s, created_at = %s
                WHERE id = %s
                """
                db.execute_query(update_query, (
                    "eligible" if eligibility_data["eligible"] else "not_eligible",
                    json.dumps(eligibility_data),
                    datetime.utcnow(),
                    existing[0]["id"]
                ))
            else:
                # Insert new record
                insert_query = """
                INSERT INTO government_schemes (citizen_id, scheme_name, scheme_id, 
                                              eligibility_status, benefits_availed, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                db.execute_query(insert_query, (
                    citizen_id,
                    scheme_name,
                    eligibility_data.get("scheme_id"),
                    "eligible" if eligibility_data["eligible"] else "not_eligible",
                    json.dumps(eligibility_data),
                    datetime.utcnow()
                ))
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Scheme eligibility save failed: {str(e)}")
            return False
    
    async def get_vaccination_centers(self, district, date=None):
        """Get vaccination centers from CoWIN API"""
        try:
            # Mock CoWIN API response (replace with actual API)
            centers = [
                {
                    "name": "PHC Koraput",
                    "address": "Main Road, Koraput",
                    "district": district,
                    "pincode": "764020",
                    "available_vaccines": ["COVISHIELD", "COVAXIN"],
                    "available_slots": 50,
                    "timing": "9:00 AM - 5:00 PM"
                },
                {
                    "name": "CHC Jeypore",
                    "address": "Hospital Road, Jeypore",
                    "district": district,
                    "pincode": "764001",
                    "available_vaccines": ["COVISHIELD"],
                    "available_slots": 30,
                    "timing": "10:00 AM - 4:00 PM"
                }
            ]
            
            return {
                "success": True,
                "centers": centers,
                "date": date or datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            current_app.logger.error(f"Vaccination centers fetch failed: {str(e)}")
            return {
                "success": False,
                "error": "Failed to fetch vaccination centers"
            }
    
    async def create_abha_id(self, citizen_data):
        """Create ABHA ID for citizen"""
        try:
            # Mock ABHA creation (replace with actual ABDM API)
            abha_id = f"{citizen_data.get('phone', '1234567890')[-4:]}-{datetime.now().strftime('%Y%m%d')}-{citizen_data.get('user_id', 'USER')[-4:]}"
            
            abha_data = {
                "abha_id": abha_id,
                "abha_number": f"12-3456-7890-{abha_id[-4:]}",
                "status": "active",
                "created_date": datetime.now().isoformat(),
                "linked_facilities": []
            }
            
            # Update user record with ABHA ID
            update_query = "UPDATE users SET abha_id = %s WHERE id = %s"
            db.execute_query(update_query, (abha_data["abha_number"], citizen_data.get("user_id")))
            
            return {
                "success": True,
                "abha_data": abha_data
            }
            
        except Exception as e:
            current_app.logger.error(f"ABHA ID creation failed: {str(e)}")
            return {
                "success": False,
                "error": "ABHA ID creation failed"
            }
    
    async def get_scheme_benefits(self, user_id, scheme_name):
        """Get scheme benefits for user"""
        try:
            query = """
            SELECT gs.*, c.user_id
            FROM government_schemes gs
            JOIN citizens c ON gs.citizen_id = c.id
            WHERE c.user_id = %s AND gs.scheme_name = %s
            ORDER BY gs.created_at DESC
            LIMIT 1
            """
            
            result = db.execute_query(query, (user_id, scheme_name))
            
            if result:
                scheme_data = result[0]
                benefits = json.loads(scheme_data.get("benefits_availed", "{}"))
                
                return {
                    "success": True,
                    "scheme_data": {
                        "scheme_name": scheme_data["scheme_name"],
                        "eligibility_status": scheme_data["eligibility_status"],
                        "benefits": benefits,
                        "last_updated": scheme_data["created_at"].isoformat()
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "No scheme data found"
                }
                
        except Exception as e:
            current_app.logger.error(f"Scheme benefits fetch failed: {str(e)}")
            return {
                "success": False,
                "error": "Failed to fetch scheme benefits"
            }
    
    async def find_nearest_facilities(self, location_data, facility_type="all"):
        """Find nearest healthcare facilities"""
        try:
            base_query = """
            SELECT *, 
                   (6371 * acos(cos(radians(%s)) * cos(radians(CAST(coordinates->>'lat' AS FLOAT))) 
                   * cos(radians(CAST(coordinates->>'lng' AS FLOAT)) - radians(%s)) 
                   + sin(radians(%s)) * sin(radians(CAST(coordinates->>'lat' AS FLOAT))))) AS distance
            FROM healthcare_facilities
            WHERE coordinates IS NOT NULL
            """
            
            params = [
                location_data.get("latitude", 0),
                location_data.get("longitude", 0),
                location_data.get("latitude", 0)
            ]
            
            if facility_type != "all":
                base_query += " AND type = %s"
                params.append(facility_type)
            
            base_query += " ORDER BY distance LIMIT 10"
            
            facilities = db.execute_query(base_query, params)
            
            return {
                "success": True,
                "facilities": facilities or [],
                "location": location_data
            }
            
        except Exception as e:
            current_app.logger.error(f"Facility search failed: {str(e)}")
            return {
                "success": False,
                "error": "Failed to find facilities"
            }

# Global government API service instance
gov_api_service = GovernmentAPIService()