# Apna Swasthya Saathi Backend

AI-Powered Rural Healthcare Platform Backend API

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- PostgreSQL or Supabase account
- Git

### Installation

1. **Clone and setup:**
   ```bash
   cd backend
   python setup.py
   ```

2. **Activate virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Unix/Linux/macOS
   source venv/bin/activate
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

## 🏗️ Architecture

### Core Components

- **Flask Application**: RESTful API server
- **AI Services**: Hugging Face + Gemini integration
- **Database**: Supabase/PostgreSQL with comprehensive schema
- **Authentication**: JWT-based with role management
- **Government APIs**: BSKY, ABDM, CoWIN integration

### API Endpoints

#### Authentication (`/api/v1/auth`)
- `POST /register` - User registration
- `POST /login` - User login
- `POST /demo-login` - Demo login
- `GET /profile` - Get user profile
- `POST /refresh` - Refresh token

#### AI Diagnosis (`/api/v1/ai`)
- `POST /analyze-symptoms` - Symptom analysis
- `POST /voice-analysis` - Voice input processing
- `POST /vital-signs` - IoT device data processing
- `GET /diagnosis-history` - Get diagnosis history

#### Government Schemes (`/api/v1/schemes`)
- `POST /check-eligibility` - Check scheme eligibility
- `GET /bsky/hospitals` - Get BSKY hospitals
- `GET /benefits` - Get scheme benefits
- `POST /apply` - Apply for scheme

#### Insurance (`/api/v1/insurance`)
- `GET /products` - Get insurance products
- `POST /enroll` - Enroll in insurance
- `GET /policies` - Get user policies
- `POST /claim` - File insurance claim

#### Emergency (`/api/v1/emergency`)
- `POST /alert` - Create emergency alert
- `GET /alerts` - Get user alerts
- `POST /respond/<alert_id>` - Respond to alert
- `GET /contacts` - Get emergency contacts

#### Healthcare Facilities (`/api/v1/facilities`)
- `GET /search` - Search facilities
- `GET /nearby` - Get nearby facilities
- `GET /<facility_id>` - Get facility details
- `POST /directions` - Get directions

#### Chat (`/api/v1/chat`)
- `POST /start-session` - Start chat session
- `POST /send-message` - Send message
- `GET /sessions` - Get user sessions
- `POST /voice-message` - Process voice message

#### Health Records (`/api/v1/records`)
- `GET /` - Get health records
- `GET /summary` - Get health summary
- `POST /create` - Create health record
- `GET /<record_id>` - Get specific record
- `PUT /<record_id>` - Update record

## 🔧 Configuration

### Environment Variables

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key
HOST=0.0.0.0
PORT=5000

# Database (Choose one)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
# OR
DATABASE_URL=postgresql://user:pass@localhost/db

# AI Services
GEMINI_API_KEY=your-gemini-api-key
HUGGINGFACE_API_KEY=your-hf-token

# Government APIs
BSKY_API_URL=https://bsky.odisha.gov.in/api
ABDM_API_URL=https://dev.abdm.gov.in
```

### Database Schema

The application automatically creates the following tables:

- `users` - User accounts (ASHA workers, citizens, admins)
- `asha_workers` - ASHA worker profiles
- `citizens` - Citizen profiles
- `health_records` - Health records and diagnoses
- `ai_diagnoses` - AI analysis results
- `government_schemes` - Government scheme applications
- `insurance_policies` - Insurance policies and claims
- `emergency_alerts` - Emergency alerts and responses
- `healthcare_facilities` - Healthcare facility directory
- `chat_sessions` - Chat conversation history

## 🤖 AI Integration

### Supported Models

1. **Gemini API**: Primary AI for health analysis
2. **Hugging Face Models**: 
   - Symptom classification
   - Text processing
   - Multilingual support

### Features

- Symptom analysis and risk assessment
- Voice input processing (Hindi, English, Odia)
- Medical knowledge base matching
- Confidence scoring and recommendations

## 🏥 Government Integration

### Supported Schemes

- **BSKY (Biju Swasthya Kalyan Yojana)**
- **PMJAY (Pradhan Mantri Jan Arogya Yojana)**
- **NIRAMAYA Scheme**

### Features

- Eligibility verification
- Hospital empanelment checking
- Benefit tracking
- Application processing

## 🚨 Emergency System

### Alert Types

- Medical emergencies
- Accidents
- Breathing difficulties
- Pregnancy emergencies

### Response Flow

1. Citizen creates alert
2. Nearby ASHA workers notified
3. Response coordination
4. Resolution tracking

## 📱 Demo Credentials

For testing purposes:

```
ASHA Worker:
Email: asha@demo.com
Password: demo123

Citizen:
Email: citizen@demo.com
Password: demo123
```

## 🧪 Testing

### API Testing

```bash
# Health check
curl http://localhost:5000/health

# Demo login
curl -X POST http://localhost:5000/api/v1/auth/demo-login \
  -H "Content-Type: application/json" \
  -d '{"user_type": "citizen"}'

# Symptom analysis
curl -X POST http://localhost:5000/api/v1/ai/analyze-symptoms \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symptoms": ["fever", "headache"]}'
```

### Load Testing

```bash
# Install dependencies
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:5000
```

## 📊 Monitoring

### Logging

- Application logs: `logs/apna_swasthya.log`
- Error tracking with rotation
- Performance monitoring

### Health Checks

- `/health` - Basic health check
- Database connectivity
- AI service availability

## 🔒 Security

### Authentication

- JWT-based authentication
- Role-based access control
- Token refresh mechanism

### Data Protection

- ABDM compliance
- DPDPA compliance
- Encrypted sensitive data
- Audit logging

## 🚀 Deployment

### Production Setup

1. **Environment Configuration:**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=strong-production-key
   ```

2. **Database Migration:**
   ```bash
   python -c "from models.database import create_tables; create_tables()"
   ```

3. **Process Management:**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 📈 Performance

### Optimization

- Database indexing
- Query optimization
- Caching with Redis
- Rate limiting

### Scalability

- Horizontal scaling support
- Load balancer ready
- Microservice architecture

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- Documentation: `/docs`
- Issues: GitHub Issues
- Email: support@apnaswasthyasaathi.com

---

**Built with ❤️ for rural India's healthcare transformation**