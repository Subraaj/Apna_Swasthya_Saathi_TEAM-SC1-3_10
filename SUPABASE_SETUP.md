# Supabase Setup Guide for Apna Swasthya Saathi

## 🚀 Quick Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project"
3. Create a new organization (if needed)
4. Create a new project:
   - **Name**: `apna-swasthya-saathi`
   - **Database Password**: Choose a strong password
   - **Region**: Choose closest to your location

### 2. Get Project Credentials

After project creation, go to **Settings > API**:

- **Project URL**: `https://your-project-id.supabase.co`
- **Anon Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- **Service Role Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### 3. Configure Environment Variables

Create `.env` file in project root:

```bash
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

### 4. Run Database Migrations

In Supabase Dashboard:

1. Go to **SQL Editor**
2. Copy and paste the content from `supabase/migrations/001_initial_schema.sql`
3. Click **Run**
4. Copy and paste the content from `supabase/migrations/002_demo_data.sql`
5. Click **Run**

### 5. Enable Authentication

In Supabase Dashboard:

1. Go to **Authentication > Settings**
2. **Site URL**: `http://localhost:5173` (for development)
3. **Redirect URLs**: Add `http://localhost:5173/**`
4. **Email Auth**: Enable
5. **Confirm email**: Disable (for demo purposes)

### 6. Configure Row Level Security

The migrations automatically set up RLS policies, but verify in **Authentication > Policies**:

- ✅ Users can read/update own data
- ✅ Citizens can access own health records
- ✅ ASHA workers can access assigned patients
- ✅ Emergency alerts are properly secured

## 📊 Database Schema Overview

### Core Tables

1. **users** - User accounts and profiles
2. **asha_workers** - ASHA worker specific data
3. **citizens** - Citizen specific data
4. **health_records** - Medical records and diagnoses
5. **ai_diagnoses** - AI analysis results
6. **government_schemes** - Scheme applications and benefits
7. **insurance_policies** - Insurance policies and claims
8. **emergency_alerts** - Emergency situations and responses
9. **healthcare_facilities** - Healthcare facility directory
10. **chat_sessions** - AI chat conversations

### Key Relationships

- Users → ASHA Workers / Citizens (1:1)
- Citizens → Health Records (1:many)
- Health Records → AI Diagnoses (1:1)
- Citizens → Emergency Alerts (1:many)
- Citizens → Insurance Policies (1:many)
- Users → Chat Sessions (1:many)

## 🔐 Security Features

### Row Level Security (RLS)

- **Users**: Can only access their own data
- **Health Records**: Citizens see own records, ASHA workers see assigned patients
- **Emergency Alerts**: Citizens see own alerts, ASHA workers see area alerts
- **Insurance**: Citizens see own policies only
- **Chat Sessions**: Users see own conversations only

### Authentication Flow

1. **Registration**: Creates auth user + profile in users table
2. **Login**: Authenticates and returns user profile
3. **Demo Login**: Uses pre-created demo accounts
4. **JWT Tokens**: Automatic token management by Supabase

## 🧪 Demo Data

### Demo Accounts

**ASHA Worker:**
- Email: `asha@demo.com`
- Password: `demo123`
- Profile: Priya Patel, Koraput District

**Citizen:**
- Email: `citizen@demo.com`
- Password: `demo123`
- Profile: Ramesh Kumar, ABHA ID: 12-3456-7890-1234

### Sample Data Included

- ✅ Health records with AI diagnoses
- ✅ Insurance policy with claims
- ✅ Emergency alert history
- ✅ Government scheme applications
- ✅ Healthcare facilities directory
- ✅ Chat conversation history

## 🔧 Development Workflow

### Local Development

1. **Start Frontend**: `npm run dev`
2. **Test Authentication**: Use demo credentials
3. **Test Features**: All services connected to Supabase
4. **Monitor Database**: Use Supabase Dashboard

### Database Changes

1. **Schema Changes**: Create new migration files
2. **Test Locally**: Run migrations in development
3. **Deploy**: Apply migrations to production

### API Testing

Use Supabase Dashboard **API** section to test:

- **Authentication**: Sign up/in endpoints
- **Database**: CRUD operations
- **Real-time**: Live data updates

## 📈 Performance Optimization

### Indexes Created

- Email and ABHA ID lookups
- Health records by citizen and date
- Emergency alerts by status
- Facilities by district and type
- Chat sessions by user

### Query Optimization

- **Joins**: Optimized foreign key relationships
- **Filtering**: Efficient WHERE clauses
- **Pagination**: LIMIT/OFFSET for large datasets
- **Real-time**: Selective subscriptions

## 🚀 Production Deployment

### Environment Setup

```bash
# Production Environment Variables
VITE_SUPABASE_URL=https://your-prod-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-prod-anon-key
```

### Security Checklist

- ✅ RLS policies enabled on all tables
- ✅ API keys secured in environment variables
- ✅ Email confirmation enabled (production)
- ✅ Rate limiting configured
- ✅ Backup strategy in place

### Monitoring

- **Dashboard**: Monitor usage and performance
- **Logs**: Track API calls and errors
- **Alerts**: Set up monitoring alerts
- **Backups**: Automatic daily backups

## 🆘 Troubleshooting

### Common Issues

1. **Connection Failed**: Check URL and API keys
2. **RLS Errors**: Verify user authentication
3. **Migration Errors**: Check SQL syntax and dependencies
4. **Auth Issues**: Verify email/password and user existence

### Debug Tools

- **Supabase Dashboard**: Real-time logs and metrics
- **Browser DevTools**: Network requests and responses
- **SQL Editor**: Direct database queries
- **API Docs**: Auto-generated API documentation

## 📞 Support

- **Documentation**: [supabase.com/docs](https://supabase.com/docs)
- **Community**: [Discord](https://discord.supabase.com)
- **GitHub**: [github.com/supabase/supabase](https://github.com/supabase/supabase)

---

**Your Supabase backend is now ready for Apna Swasthya Saathi! 🎉**