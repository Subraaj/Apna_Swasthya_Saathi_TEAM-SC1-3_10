from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import asyncio
from datetime import datetime
import uuid

from services.ai_service import ai_service
from models.database import db

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/start-session', methods=['POST'])
@jwt_required()
def start_chat_session():
    """Start a new chat session"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        language = data.get('language', 'en')
        session_type = data.get('session_type', 'health_consultation')
        
        # Create new chat session
        session_id = str(uuid.uuid4())
        
        session_data = {
            'session_id': session_id,
            'session_type': session_type,
            'language': language,
            'messages': [],
            'context': {
                'user_symptoms': [],
                'current_topic': None,
                'assessment_stage': 'initial'
            },
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Save session to database
        query = """
        INSERT INTO chat_sessions (id, user_id, session_data, language, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        db.execute_query(query, (
            session_id,
            user_id,
            json.dumps(session_data),
            language,
            datetime.utcnow()
        ))
        
        # Generate welcome message
        welcome_message = generate_welcome_message(language, session_type)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'welcome_message': welcome_message,
            'language': language,
            'session_type': session_type
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Chat session start failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to start chat session'
        }), 500

@chat_bp.route('/send-message', methods=['POST'])
@jwt_required()
def send_message():
    """Send message in chat session"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        session_id = data.get('session_id')
        message = data.get('message')
        message_type = data.get('message_type', 'text')  # text, voice, image
        
        if not session_id or not message:
            return jsonify({'error': 'Session ID and message are required'}), 400
        
        # Get chat session
        session_query = "SELECT * FROM chat_sessions WHERE id = %s AND user_id = %s"
        session_result = db.execute_query(session_query, (session_id, user_id))
        
        if not session_result:
            return jsonify({'error': 'Chat session not found'}), 404
        
        session_data = json.loads(session_result[0]['session_data'])
        
        # Add user message to session
        user_message = {
            'id': str(uuid.uuid4()),
            'type': 'user',
            'content': message,
            'message_type': message_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        session_data['messages'].append(user_message)
        
        # Generate AI response
        ai_response = generate_ai_response(message, session_data, user_id)
        
        # Add AI response to session
        ai_message = {
            'id': str(uuid.uuid4()),
            'type': 'assistant',
            'content': ai_response['content'],
            'suggestions': ai_response.get('suggestions', []),
            'actions': ai_response.get('actions', []),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        session_data['messages'].append(ai_message)
        
        # Update session context
        session_data['context'] = ai_response.get('updated_context', session_data['context'])
        session_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Save updated session
        update_query = """
        UPDATE chat_sessions 
        SET session_data = %s, updated_at = %s 
        WHERE id = %s
        """
        
        db.execute_query(update_query, (
            json.dumps(session_data),
            datetime.utcnow(),
            session_id
        ))
        
        return jsonify({
            'success': True,
            'user_message': user_message,
            'ai_response': ai_message,
            'session_context': session_data['context']
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Send message failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to send message'
        }), 500

@chat_bp.route('/get-session/<session_id>', methods=['GET'])
@jwt_required()
def get_chat_session(session_id):
    """Get chat session data"""
    try:
        user_id = get_jwt_identity()
        
        # Get chat session
        query = "SELECT * FROM chat_sessions WHERE id = %s AND user_id = %s"
        result = db.execute_query(query, (session_id, user_id))
        
        if not result:
            return jsonify({'error': 'Chat session not found'}), 404
        
        session_data = json.loads(result[0]['session_data'])
        
        return jsonify({
            'success': True,
            'session': {
                'id': session_id,
                'language': result[0]['language'],
                'created_at': result[0]['created_at'].isoformat(),
                'updated_at': result[0]['updated_at'].isoformat() if result[0]['updated_at'] else None,
                'messages': session_data['messages'],
                'context': session_data['context']
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get chat session failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get chat session'
        }), 500

@chat_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_user_sessions():
    """Get all chat sessions for user"""
    try:
        user_id = get_jwt_identity()
        
        query = """
        SELECT id, language, created_at, updated_at, session_data
        FROM chat_sessions 
        WHERE user_id = %s 
        ORDER BY updated_at DESC, created_at DESC
        LIMIT 50
        """
        
        sessions = db.execute_query(query, (user_id,))
        
        formatted_sessions = []
        for session in sessions:
            session_data = json.loads(session['session_data'])
            
            # Get last message for preview
            last_message = None
            if session_data['messages']:
                last_message = session_data['messages'][-1]
            
            formatted_sessions.append({
                'id': session['id'],
                'language': session['language'],
                'session_type': session_data.get('session_type', 'health_consultation'),
                'created_at': session['created_at'].isoformat(),
                'updated_at': session['updated_at'].isoformat() if session['updated_at'] else None,
                'message_count': len(session_data['messages']),
                'last_message': last_message,
                'context': session_data.get('context', {})
            })
        
        return jsonify({
            'success': True,
            'sessions': formatted_sessions,
            'total_count': len(formatted_sessions)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user sessions failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get chat sessions'
        }), 500

@chat_bp.route('/voice-message', methods=['POST'])
@jwt_required()
def process_voice_message():
    """Process voice message in chat"""
    try:
        user_id = get_jwt_identity()
        
        if 'audio' not in request.files:
            return jsonify({'error': 'Audio file is required'}), 400
        
        audio_file = request.files['audio']
        session_id = request.form.get('session_id')
        language = request.form.get('language', 'hi')
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Process audio to text (mock implementation)
        transcribed_text = process_voice_input(audio_file, language)
        
        if not transcribed_text:
            return jsonify({'error': 'Could not process voice input'}), 400
        
        # Send transcribed text as regular message
        message_data = {
            'session_id': session_id,
            'message': transcribed_text,
            'message_type': 'voice'
        }
        
        # Use existing send_message logic
        return send_message_internal(user_id, message_data)
        
    except Exception as e:
        current_app.logger.error(f"Voice message processing failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Voice message processing failed'
        }), 500

def generate_welcome_message(language, session_type):
    """Generate welcome message based on language and session type"""
    welcome_messages = {
        'en': {
            'health_consultation': "Hello! I'm your AI health assistant. I'm here to help you with your health concerns. Please tell me about your symptoms or health questions.",
            'emergency': "This is emergency assistance. Please describe your emergency situation immediately. If this is life-threatening, please call 108 right away.",
            'general': "Hello! I'm here to help you with health information and guidance. How can I assist you today?"
        },
        'hi': {
            'health_consultation': "नमस्ते! मैं आपका AI स्वास्थ्य सहायक हूं। मैं आपकी स्वास्थ्य समस्याओं में मदद करने के लिए यहां हूं। कृपया अपने लक्षणों या स्वास्थ्य प्रश्नों के बारे में बताएं।",
            'emergency': "यह आपातकालीन सहायता है। कृपया तुरंत अपनी आपातकालीन स्थिति का वर्णन करें। यदि यह जीवन के लिए खतरनाक है, तो कृपया तुरंत 108 पर कॉल करें।",
            'general': "नमस्ते! मैं स्वास्थ्य जानकारी और मार्गदर्शन में आपकी मदद करने के लिए यहां हूं। आज मैं आपकी कैसे सहायता कर सकता हूं?"
        },
        'or': {
            'health_consultation': "ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କର AI ସ୍ୱାସ୍ଥ୍ୟ ସହାୟକ। ମୁଁ ଆପଣଙ୍କର ସ୍ୱାସ୍ଥ୍ୟ ସମସ୍ୟାରେ ସାହାଯ୍ୟ କରିବା ପାଇଁ ଏଠାରେ ଅଛି। ଦୟାକରି ଆପଣଙ୍କର ଲକ୍ଷଣ କିମ୍ବା ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରଶ୍ନ ବିଷୟରେ କୁହନ୍ତୁ।",
            'emergency': "ଏହା ଜରୁରୀକାଲୀନ ସହାୟତା। ଦୟାକରି ତୁରନ୍ତ ଆପଣଙ୍କର ଜରୁରୀକାଲୀନ ପରିସ୍ଥିତି ବର୍ଣ୍ଣନା କରନ୍ତୁ। ଯଦି ଏହା ଜୀବନ ପ୍ରତି ବିପଦଜନକ, ତେବେ ଦୟାକରି ତୁରନ୍ତ 108 କୁ କଲ କରନ୍ତୁ।",
            'general': "ନମସ୍କାର! ମୁଁ ସ୍ୱାସ୍ଥ୍ୟ ସୂଚନା ଏବଂ ମାର୍ଗଦର୍ଶନରେ ଆପଣଙ୍କୁ ସାହାଯ୍ୟ କରିବା ପାଇଁ ଏଠାରେ ଅଛି। ଆଜି ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?"
        }
    }
    
    return welcome_messages.get(language, welcome_messages['en']).get(session_type, welcome_messages[language]['general'])

def generate_ai_response(message, session_data, user_id):
    """Generate AI response to user message"""
    try:
        context = session_data.get('context', {})
        language = session_data.get('language', 'en')
        messages_history = session_data.get('messages', [])
        
        # Analyze message for health-related content
        health_keywords = extract_health_keywords(message, language)
        
        # Update context with new information
        if health_keywords:
            context['user_symptoms'].extend(health_keywords)
            context['current_topic'] = 'symptom_assessment'
        
        # Generate response based on context and message
        if context.get('current_topic') == 'symptom_assessment':
            response = generate_symptom_response(message, context, language)
        elif 'emergency' in message.lower() or 'urgent' in message.lower():
            response = generate_emergency_response(message, language)
        else:
            response = generate_general_health_response(message, context, language)
        
        # Add suggestions and actions
        suggestions = generate_suggestions(context, language)
        actions = generate_actions(context, health_keywords)
        
        return {
            'content': response,
            'suggestions': suggestions,
            'actions': actions,
            'updated_context': context
        }
        
    except Exception as e:
        current_app.logger.error(f"AI response generation failed: {str(e)}")
        return {
            'content': get_fallback_response(language),
            'suggestions': [],
            'actions': [],
            'updated_context': context
        }

def extract_health_keywords(message, language):
    """Extract health-related keywords from message"""
    health_keywords_map = {
        'en': {
            'fever': 'fever',
            'headache': 'headache',
            'cough': 'cough',
            'pain': 'pain',
            'tired': 'fatigue',
            'weak': 'weakness',
            'dizzy': 'dizziness',
            'nausea': 'nausea',
            'vomit': 'vomiting'
        },
        'hi': {
            'बुखार': 'fever',
            'सिरदर्द': 'headache',
            'खांसी': 'cough',
            'दर्द': 'pain',
            'थकान': 'fatigue',
            'कमजोर': 'weakness',
            'चक्कर': 'dizziness',
            'उल्टी': 'nausea'
        },
        'or': {
            'ଜ୍ୱର': 'fever',
            'ମୁଣ୍ଡବିନ୍ଧା': 'headache',
            'କାଶ': 'cough',
            'ଯନ୍ତ୍ରଣା': 'pain',
            'ଦୁର୍ବଳତା': 'weakness'
        }
    }
    
    keywords = health_keywords_map.get(language, health_keywords_map['en'])
    found_keywords = []
    
    message_lower = message.lower()
    for keyword, symptom in keywords.items():
        if keyword.lower() in message_lower:
            found_keywords.append(symptom)
    
    return found_keywords

def generate_symptom_response(message, context, language):
    """Generate response for symptom assessment"""
    responses = {
        'en': [
            "I understand you're experiencing some symptoms. Can you tell me more about when these symptoms started?",
            "Thank you for sharing that information. Are you experiencing any other symptoms along with this?",
            "Based on what you've told me, I recommend consulting with your ASHA worker or visiting a healthcare facility.",
            "It's important to monitor these symptoms. Have you taken your temperature or checked any vital signs?"
        ],
        'hi': [
            "मैं समझ गया हूं कि आप कुछ लक्षणों का अनुभव कर रहे हैं। क्या आप मुझे बता सकते हैं कि ये लक्षण कब शुरू हुए?",
            "इस जानकारी को साझा करने के लिए धन्यवाद। क्या आप इसके साथ कोई अन्य लक्षण भी महसूस कर रहे हैं?",
            "आपने जो बताया है उसके आधार पर, मैं आपके ASHA कार्यकर्ता से सलाह लेने या स्वास्थ्य सुविधा में जाने की सलाह देता हूं।",
            "इन लक्षणों पर नज़र रखना महत्वपूर्ण है। क्या आपने अपना तापमान लिया है या कोई महत्वपूर्ण संकेत जांचे हैं?"
        ]
    }
    
    response_list = responses.get(language, responses['en'])
    # Simple logic to cycle through responses based on conversation stage
    message_count = len(context.get('user_symptoms', []))
    response_index = min(message_count, len(response_list) - 1)
    
    return response_list[response_index]

def generate_emergency_response(message, language):
    """Generate emergency response"""
    emergency_responses = {
        'en': "This sounds like it could be an emergency. Please call 108 immediately for ambulance service, or contact your nearest ASHA worker. If you're experiencing severe symptoms, don't wait - seek immediate medical attention.",
        'hi': "यह एक आपातकाल हो सकता है। कृपया एम्बुलेंस सेवा के लिए तुरंत 108 पर कॉल करें, या अपने निकटतम ASHA कार्यकर्ता से संपर्क करें। यदि आप गंभीर लक्षणों का अनुभव कर रहे हैं, तो प्रतीक्षा न करें - तुरंत चिकित्सा सहायता लें।",
        'or': "ଏହା ଏକ ଜରୁରୀକାଳୀନ ପରିସ୍ଥିତି ହୋଇପାରେ। ଦୟାକରି ଆମ୍ବୁଲାନ୍ସ ସେବା ପାଇଁ ତୁରନ୍ତ 108 କୁ କଲ କରନ୍ତୁ, କିମ୍ବା ଆପଣଙ୍କର ନିକଟତମ ASHA କର୍ମୀଙ୍କ ସହିତ ଯୋଗାଯୋଗ କରନ୍ତୁ।"
    }
    
    return emergency_responses.get(language, emergency_responses['en'])

def generate_general_health_response(message, context, language):
    """Generate general health response"""
    general_responses = {
        'en': "I'm here to help with your health concerns. Please feel free to share any symptoms you're experiencing, ask about health conditions, or inquire about healthcare services in your area.",
        'hi': "मैं आपकी स्वास्थ्य चिंताओं में मदद करने के लिए यहां हूं। कृपया बेझिझक कोई भी लक्षण साझा करें जिसका आप अनुभव कर रहे हैं, स्वास्थ्य स्थितियों के बारे में पूछें, या अपने क्षेत्र में स्वास्थ्य सेवाओं के बारे में पूछताछ करें।",
        'or': "ମୁଁ ଆପଣଙ୍କର ସ୍ୱାସ୍ଥ୍ୟ ଚିନ୍ତାରେ ସାହାଯ୍ୟ କରିବା ପାଇଁ ଏଠାରେ ଅଛି। ଦୟାକରି ଆପଣ ଅନୁଭବ କରୁଥିବା କୌଣସି ଲକ୍ଷଣ ସାଝା କରନ୍ତୁ, ସ୍ୱାସ୍ଥ୍ୟ ଅବସ୍ଥା ବିଷୟରେ ପଚାରନ୍ତୁ।"
    }
    
    return general_responses.get(language, general_responses['en'])

def generate_suggestions(context, language):
    """Generate conversation suggestions"""
    suggestions_map = {
        'en': [
            "Tell me about your symptoms",
            "Find nearby healthcare facilities",
            "Check government health schemes",
            "Emergency assistance",
            "Health tips and advice"
        ],
        'hi': [
            "अपने लक्षणों के बारे में बताएं",
            "नजदीकी स्वास्थ्य सुविधाएं खोजें",
            "सरकारी स्वास्थ्य योजनाएं देखें",
            "आपातकालीन सहायता",
            "स्वास्थ्य सुझाव और सलाह"
        ]
    }
    
    return suggestions_map.get(language, suggestions_map['en'])

def generate_actions(context, health_keywords):
    """Generate actionable items based on context"""
    actions = []
    
    if health_keywords:
        actions.append({
            'type': 'symptom_analysis',
            'label': 'Analyze Symptoms',
            'description': 'Get AI analysis of your symptoms'
        })
    
    actions.append({
        'type': 'find_facilities',
        'label': 'Find Healthcare',
        'description': 'Locate nearby healthcare facilities'
    })
    
    actions.append({
        'type': 'emergency_alert',
        'label': 'Emergency Help',
        'description': 'Get immediate emergency assistance'
    })
    
    return actions

def get_fallback_response(language):
    """Get fallback response when AI fails"""
    fallback_responses = {
        'en': "I apologize, but I'm having trouble processing your request right now. Please contact your ASHA worker or visit the nearest healthcare facility for assistance.",
        'hi': "मुझे खेद है, लेकिन मुझे अभी आपके अनुरोध को संसाधित करने में परेशानी हो रही है। कृपया सहायता के लिए अपने ASHA कार्यकर्ता से संपर्क करें या निकटतम स्वास्थ्य सुविधा में जाएं।",
        'or': "ମୁଁ କ୍ଷମା ପ୍ରାର୍ଥନା କରୁଛି, କିନ୍ତୁ ମୁଁ ବର୍ତ୍ତମାନ ଆପଣଙ୍କର ଅନୁରୋଧ ପ୍ରକ୍ରିୟାକରଣରେ ଅସୁବିଧା ଭୋଗୁଛି। ଦୟାକରି ସହାୟତା ପାଇଁ ଆପଣଙ୍କର ASHA କର୍ମୀଙ୍କ ସହିତ ଯୋଗାଯୋଗ କରନ୍ତୁ।"
    }
    
    return fallback_responses.get(language, fallback_responses['en'])

def process_voice_input(audio_file, language):
    """Process voice input (mock implementation)"""
    # Mock transcription - replace with actual speech-to-text service
    mock_transcriptions = {
        'hi': 'मुझे बुखार और सिरदर्द है',
        'en': 'I have fever and headache',
        'or': 'ମୋର ଜ୍ୱର ଓ ମୁଣ୍ଡବିନ୍ଧା ହେଉଛି'
    }
    
    return mock_transcriptions.get(language, mock_transcriptions['en'])

def send_message_internal(user_id, message_data):
    """Internal method to send message (used by voice processing)"""
    # This would call the main send_message logic
    # For now, return a simple response
    return jsonify({
        'success': True,
        'message': 'Voice message processed successfully',
        'transcribed_text': message_data['message']
    }), 200