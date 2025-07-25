import requests
import json
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from flask import current_app
from models.database import db
import uuid
from datetime import datetime

class AIHealthService:
    def __init__(self):
        self.symptom_classifier = None
        self.health_embedder = None
        self.disease_knowledge_base = self._load_disease_knowledge()
        self.gemini_api_key = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize AI models"""
        try:
            # Initialize Hugging Face models
            self.symptom_classifier = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                return_all_scores=True
            )
            
            # Initialize sentence transformer for semantic similarity
            self.health_embedder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Get Gemini API key from config
            self.gemini_api_key = current_app.config.get('GEMINI_API_KEY')
            
            current_app.logger.info("AI models initialized successfully")
            
        except Exception as e:
            current_app.logger.error(f"AI model initialization failed: {str(e)}")
    
    def _load_disease_knowledge(self):
        """Load disease knowledge base"""
        return {
            "anemia": {
                "symptoms": ["fatigue", "weakness", "pale skin", "shortness of breath", "dizziness"],
                "risk_factors": ["poor nutrition", "pregnancy", "heavy menstruation"],
                "severity_indicators": ["hemoglobin < 7", "severe fatigue", "chest pain"],
                "recommendations": ["iron supplements", "dietary changes", "medical consultation"]
            },
            "hypertension": {
                "symptoms": ["headache", "dizziness", "chest pain", "shortness of breath"],
                "risk_factors": ["age > 40", "obesity", "smoking", "family history"],
                "severity_indicators": ["bp > 180/120", "severe headache", "vision problems"],
                "recommendations": ["lifestyle changes", "medication", "regular monitoring"]
            },
            "diabetes": {
                "symptoms": ["excessive thirst", "frequent urination", "fatigue", "blurred vision"],
                "risk_factors": ["obesity", "family history", "sedentary lifestyle"],
                "severity_indicators": ["blood sugar > 300", "ketones in urine", "confusion"],
                "recommendations": ["blood sugar monitoring", "medication", "diet control"]
            },
            "respiratory_infection": {
                "symptoms": ["cough", "fever", "sore throat", "runny nose", "body aches"],
                "risk_factors": ["seasonal changes", "crowded places", "poor immunity"],
                "severity_indicators": ["high fever > 102F", "difficulty breathing", "chest pain"],
                "recommendations": ["rest", "hydration", "symptomatic treatment", "medical consultation if severe"]
            }
        }
    
    async def analyze_symptoms(self, symptoms_data, vital_signs=None, user_id=None):
        """Analyze symptoms using AI models"""
        try:
            # Prepare input data
            symptoms_text = self._prepare_symptoms_text(symptoms_data)
            
            # Get AI predictions
            predictions = await self._get_ai_predictions(symptoms_text, vital_signs)
            
            # Calculate risk level
            risk_level = self._calculate_risk_level(predictions, vital_signs)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(predictions, risk_level)
            
            # Save AI diagnosis
            diagnosis_id = await self._save_ai_diagnosis(
                user_id, symptoms_data, predictions, vital_signs
            )
            
            return {
                "diagnosis_id": diagnosis_id,
                "predictions": predictions,
                "risk_level": risk_level,
                "recommendations": recommendations,
                "confidence_score": predictions.get("confidence", 0.0),
                "requires_immediate_attention": risk_level in ["high", "critical"]
            }
            
        except Exception as e:
            current_app.logger.error(f"Symptom analysis failed: {str(e)}")
            return {
                "error": "Analysis failed",
                "message": "Please consult with your ASHA worker or visit nearest healthcare facility"
            }
    
    def _prepare_symptoms_text(self, symptoms_data):
        """Prepare symptoms text for AI analysis"""
        if isinstance(symptoms_data, dict):
            symptoms_list = []
            for category, symptoms in symptoms_data.items():
                if isinstance(symptoms, list):
                    symptoms_list.extend(symptoms)
                else:
                    symptoms_list.append(str(symptoms))
            return " ".join(symptoms_list)
        elif isinstance(symptoms_data, list):
            return " ".join(symptoms_data)
        else:
            return str(symptoms_data)
    
    async def _get_ai_predictions(self, symptoms_text, vital_signs):
        """Get AI predictions from multiple sources"""
        predictions = {}
        
        try:
            # Use Gemini API for comprehensive analysis
            gemini_result = await self._query_gemini_api(symptoms_text, vital_signs)
            predictions["gemini"] = gemini_result
            
            # Use local knowledge base matching
            knowledge_result = self._match_knowledge_base(symptoms_text)
            predictions["knowledge_base"] = knowledge_result
            
            # Combine predictions
            combined_prediction = self._combine_predictions(predictions)
            
            return combined_prediction
            
        except Exception as e:
            current_app.logger.error(f"AI prediction failed: {str(e)}")
            return {"condition": "unknown", "confidence": 0.0}
    
    async def _query_gemini_api(self, symptoms_text, vital_signs):
        """Query Gemini API for health analysis"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.gemini_api_key}"
            
            prompt = f"""
            You are a medical AI assistant for rural healthcare in India. Analyze the following symptoms and vital signs:
            
            Symptoms: {symptoms_text}
            Vital Signs: {vital_signs if vital_signs else 'Not provided'}
            
            Provide a structured analysis in JSON format with:
            1. Most likely condition
            2. Confidence score (0-1)
            3. Risk level (low/medium/high/critical)
            4. Immediate actions needed
            5. When to seek medical care
            
            Focus on common conditions in rural India and be conservative in recommendations.
            """
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                
                # Try to parse JSON from response
                try:
                    return json.loads(content)
                except:
                    # If not JSON, create structured response
                    return {
                        "condition": "requires_assessment",
                        "confidence": 0.7,
                        "analysis": content,
                        "source": "gemini"
                    }
            else:
                return {"condition": "analysis_unavailable", "confidence": 0.0}
                
        except Exception as e:
            current_app.logger.error(f"Gemini API query failed: {str(e)}")
            return {"condition": "analysis_failed", "confidence": 0.0}
    
    def _match_knowledge_base(self, symptoms_text):
        """Match symptoms against knowledge base"""
        try:
            # Create embeddings for input symptoms
            input_embedding = self.health_embedder.encode([symptoms_text])
            
            best_match = None
            best_score = 0.0
            
            for condition, data in self.disease_knowledge_base.items():
                # Create embedding for condition symptoms
                condition_text = " ".join(data["symptoms"])
                condition_embedding = self.health_embedder.encode([condition_text])
                
                # Calculate similarity
                similarity = cosine_similarity(input_embedding, condition_embedding)[0][0]
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = condition
            
            if best_match and best_score > 0.3:  # Threshold for meaningful match
                return {
                    "condition": best_match,
                    "confidence": float(best_score),
                    "details": self.disease_knowledge_base[best_match],
                    "source": "knowledge_base"
                }
            else:
                return {"condition": "unknown", "confidence": 0.0}
                
        except Exception as e:
            current_app.logger.error(f"Knowledge base matching failed: {str(e)}")
            return {"condition": "matching_failed", "confidence": 0.0}
    
    def _combine_predictions(self, predictions):
        """Combine predictions from multiple sources"""
        try:
            gemini_pred = predictions.get("gemini", {})
            kb_pred = predictions.get("knowledge_base", {})
            
            # Weight the predictions
            gemini_weight = 0.7
            kb_weight = 0.3
            
            # Combine confidence scores
            gemini_conf = gemini_pred.get("confidence", 0.0)
            kb_conf = kb_pred.get("confidence", 0.0)
            
            combined_confidence = (gemini_conf * gemini_weight + kb_conf * kb_weight)
            
            # Determine primary condition
            if gemini_conf > kb_conf:
                primary_condition = gemini_pred.get("condition", "unknown")
                primary_source = "gemini"
            else:
                primary_condition = kb_pred.get("condition", "unknown")
                primary_source = "knowledge_base"
            
            return {
                "condition": primary_condition,
                "confidence": combined_confidence,
                "primary_source": primary_source,
                "all_predictions": predictions
            }
            
        except Exception as e:
            current_app.logger.error(f"Prediction combination failed: {str(e)}")
            return {"condition": "combination_failed", "confidence": 0.0}
    
    def _calculate_risk_level(self, predictions, vital_signs):
        """Calculate risk level based on predictions and vital signs"""
        try:
            base_risk = "low"
            
            # Check confidence level
            confidence = predictions.get("confidence", 0.0)
            if confidence < 0.3:
                return "unknown"
            
            # Check vital signs for critical values
            if vital_signs:
                if self._has_critical_vitals(vital_signs):
                    return "critical"
                elif self._has_concerning_vitals(vital_signs):
                    base_risk = "high"
            
            # Check condition severity
            condition = predictions.get("condition", "")
            if condition in ["anemia", "hypertension", "diabetes"]:
                if confidence > 0.8:
                    base_risk = "high" if base_risk == "low" else base_risk
                else:
                    base_risk = "medium" if base_risk == "low" else base_risk
            
            return base_risk
            
        except Exception as e:
            current_app.logger.error(f"Risk calculation failed: {str(e)}")
            return "unknown"
    
    def _has_critical_vitals(self, vital_signs):
        """Check for critical vital signs"""
        try:
            if isinstance(vital_signs, dict):
                # Blood pressure
                if "systolic_bp" in vital_signs and vital_signs["systolic_bp"] > 180:
                    return True
                if "diastolic_bp" in vital_signs and vital_signs["diastolic_bp"] > 120:
                    return True
                
                # Heart rate
                if "heart_rate" in vital_signs:
                    hr = vital_signs["heart_rate"]
                    if hr < 50 or hr > 120:
                        return True
                
                # Temperature
                if "temperature" in vital_signs and vital_signs["temperature"] > 103:
                    return True
                
                # Hemoglobin
                if "hemoglobin" in vital_signs and vital_signs["hemoglobin"] < 7:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _has_concerning_vitals(self, vital_signs):
        """Check for concerning vital signs"""
        try:
            if isinstance(vital_signs, dict):
                # Mild hypertension
                if "systolic_bp" in vital_signs and vital_signs["systolic_bp"] > 140:
                    return True
                
                # Mild anemia
                if "hemoglobin" in vital_signs and vital_signs["hemoglobin"] < 10:
                    return True
                
                # Fever
                if "temperature" in vital_signs and vital_signs["temperature"] > 100:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _generate_recommendations(self, predictions, risk_level):
        """Generate recommendations based on analysis"""
        try:
            recommendations = []
            
            condition = predictions.get("condition", "")
            
            # Risk-based recommendations
            if risk_level == "critical":
                recommendations.extend([
                    "Seek immediate medical attention",
                    "Call emergency services (108)",
                    "Contact your ASHA worker immediately"
                ])
            elif risk_level == "high":
                recommendations.extend([
                    "Consult with healthcare provider within 24 hours",
                    "Monitor symptoms closely",
                    "Contact ASHA worker for guidance"
                ])
            elif risk_level == "medium":
                recommendations.extend([
                    "Schedule appointment with healthcare provider",
                    "Monitor symptoms for changes",
                    "Follow up with ASHA worker"
                ])
            else:
                recommendations.extend([
                    "Continue monitoring symptoms",
                    "Maintain healthy lifestyle",
                    "Consult ASHA worker if symptoms worsen"
                ])
            
            # Condition-specific recommendations
            if condition in self.disease_knowledge_base:
                condition_recs = self.disease_knowledge_base[condition].get("recommendations", [])
                recommendations.extend(condition_recs)
            
            # General health recommendations
            recommendations.extend([
                "Maintain proper hydration",
                "Get adequate rest",
                "Follow balanced diet"
            ])
            
            return list(set(recommendations))  # Remove duplicates
            
        except Exception as e:
            current_app.logger.error(f"Recommendation generation failed: {str(e)}")
            return ["Consult with your ASHA worker or healthcare provider"]
    
    async def _save_ai_diagnosis(self, user_id, symptoms_data, predictions, vital_signs):
        """Save AI diagnosis to database"""
        try:
            diagnosis_id = str(uuid.uuid4())
            
            query = """
            INSERT INTO ai_diagnoses (id, health_record_id, model_used, input_data, 
                                    prediction_results, confidence_score, processing_time_ms, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            input_data = {
                "symptoms": symptoms_data,
                "vital_signs": vital_signs,
                "user_id": user_id
            }
            
            params = (
                diagnosis_id,
                None,  # health_record_id will be set when health record is created
                "gemini_knowledge_hybrid",
                json.dumps(input_data),
                json.dumps(predictions),
                predictions.get("confidence", 0.0),
                100,  # Placeholder processing time
                datetime.utcnow()
            )
            
            db.execute_query(query, params)
            return diagnosis_id
            
        except Exception as e:
            current_app.logger.error(f"AI diagnosis save failed: {str(e)}")
            return None

# Global AI service instance
ai_service = AIHealthService()