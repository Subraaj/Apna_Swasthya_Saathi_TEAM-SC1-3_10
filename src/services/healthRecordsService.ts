import { supabase } from '../lib/supabase'
import type { HealthRecord } from '../lib/supabase'

export interface HealthSummary {
  patient_info: any
  recent_activity: any
  latest_vitals: any
  risk_assessment: any
  medications: any[]
  health_trends: any[]
  recommendations: any[]
}

class HealthRecordsService {
  private getDemoHealthRecords(userId: string): HealthRecord[] {
    return [
      {
        id: '1',
        citizen_id: userId,
        asha_id: '550e8400-e29b-41d4-a716-446655440001',
        record_type: 'ai_diagnosis',
        diagnosis: {
          condition: 'anemia',
          confidence: 0.85,
          ai_analysis: { hemoglobin_level: 7.2 }
        },
        symptoms: ['fatigue', 'weakness', 'pale_skin'],
        vital_signs: {
          hemoglobin: 7.2,
          blood_pressure: '120/80',
          heart_rate: 85
        },
        recommendations: 'Iron supplementation recommended. Follow-up in 2 weeks.',
        risk_level: 'high',
        created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString()
      },
      {
        id: '2',
        citizen_id: userId,
        asha_id: '550e8400-e29b-41d4-a716-446655440001',
        record_type: 'prescription',
        diagnosis: {
          medication: 'Iron + Folic Acid',
          dosage: '1 tablet daily',
          duration: '3 months'
        },
        symptoms: ['anemia', 'iron_deficiency'],
        recommendations: 'Take with vitamin C for better absorption.',
        risk_level: 'medium',
        created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
      },
      {
        id: '3',
        citizen_id: userId,
        asha_id: '550e8400-e29b-41d4-a716-446655440001',
        record_type: 'follow_up',
        diagnosis: {
          improvement: 'moderate',
          hemoglobin: 8.5,
          compliance: 'good'
        },
        symptoms: ['improved_energy', 'less_fatigue'],
        vital_signs: {
          hemoglobin: 8.5,
          blood_pressure: '118/78',
          heart_rate: 78
        },
        recommendations: 'Continue iron supplementation. Next check in 4 weeks.',
        risk_level: 'low',
        created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString()
      }
    ]
  }

  async getHealthRecords(userId: string, filters?: any): Promise<HealthRecord[]> {
    try {
      let records = this.getDemoHealthRecords(userId)

      if (filters?.record_type && filters.record_type !== 'all') {
        records = records.filter(r => r.record_type === filters.record_type)
      }

      if (filters?.start_date) {
        records = records.filter(r => new Date(r.created_at) >= new Date(filters.start_date))
      }

      if (filters?.end_date) {
        records = records.filter(r => new Date(r.created_at) <= new Date(filters.end_date))
      }

      if (filters?.limit) {
        records = records.slice(0, filters.limit)
      }

      return records
    } catch (error) {
      console.error('Health records fetch failed:', error)
      return []
    }
  }

  async getHealthSummary(userId: string): Promise<HealthSummary | null> {
    try {
      const userData = localStorage.getItem('user_data')
      if (!userData) return null

      const user = JSON.parse(userData)
      const records = this.getDemoHealthRecords(userId)

      const summary: HealthSummary = {
        patient_info: {
          name: user.full_name,
          age: this.calculateAge('1985-05-15'),
          gender: 'Male',
          blood_group: 'B+',
          abha_id: user.abha_id
        },
        recent_activity: {
          records_last_30_days: records.length,
          record_types: this.groupRecordTypes(records)
        },
        latest_vitals: records.find(r => r.vital_signs) || null,
        risk_assessment: {
          distribution: this.getRiskDistribution(records),
          current_risk: records[0]?.risk_level || 'unknown'
        },
        medications: records.filter(r => r.record_type === 'prescription'),
        health_trends: this.getHealthTrends(records),
        recommendations: this.generateRecommendations(records)
      }

      return summary
    } catch (error) {
      console.error('Health summary generation failed:', error)
      return null
    }
  }

  async createHealthRecord(userId: string, recordData: Partial<HealthRecord>): Promise<string | null> {
    try {
      const recordId = crypto.randomUUID()
      const newRecord = {
        id: recordId,
        citizen_id: userId,
        created_at: new Date().toISOString(),
        ...recordData
      }

      const records = JSON.parse(localStorage.getItem('health_records') || '[]')
      records.push(newRecord)
      localStorage.setItem('health_records', JSON.stringify(records))

      return recordId
    } catch (error) {
      console.error('Health record creation failed:', error)
      return null
    }
  }

  async updateHealthRecord(recordId: string, userId: string, updateData: Partial<HealthRecord>): Promise<boolean> {
    try {
      const records = JSON.parse(localStorage.getItem('health_records') || '[]')
      const recordIndex = records.findIndex((r: any) => r.id === recordId && r.citizen_id === userId)

      if (recordIndex !== -1) {
        records[recordIndex] = { ...records[recordIndex], ...updateData }
        localStorage.setItem('health_records', JSON.stringify(records))
        return true
      }

      return false
    } catch (error) {
      console.error('Health record update failed:', error)
      return false
    }
  }

  async exportHealthRecords(userId: string): Promise<any> {
    try {
      const records = await this.getHealthRecords(userId)
      const summary = await this.getHealthSummary(userId)

      return {
        export_date: new Date().toISOString(),
        patient_info: summary?.patient_info,
        total_records: records.length,
        records: records
      }
    } catch (error) {
      console.error('Health records export failed:', error)
      return null
    }
  }

  private calculateAge(dateOfBirth?: string): number | null {
    if (!dateOfBirth) return null

    const today = new Date()
    const birth = new Date(dateOfBirth)
    let age = today.getFullYear() - birth.getFullYear()
    
    if (today.getMonth() < birth.getMonth() || 
        (today.getMonth() === birth.getMonth() && today.getDate() < birth.getDate())) {
      age--
    }

    return age
  }

  private groupRecordTypes(records: any[]): any[] {
    const grouped = records.reduce((acc: any, record) => {
      acc[record.record_type] = (acc[record.record_type] || 0) + 1
      return acc
    }, {})

    return Object.entries(grouped).map(([type, count]) => ({
      type,
      count,
      latest_date: records.find(r => r.record_type === type)?.created_at
    }))
  }

  private getRiskDistribution(records: any[]): any[] {
    const grouped = records.reduce((acc: any, record) => {
      if (record.risk_level) {
        acc[record.risk_level] = (acc[record.risk_level] || 0) + 1
      }
      return acc
    }, {})

    return Object.entries(grouped).map(([level, count]) => ({
      risk_level: level,
      count
    }))
  }

  private getHealthTrends(records: any[]): any[] {
    // Group by month for trends
    const monthlyData = records.reduce((acc: any, record) => {
      const month = new Date(record.created_at).toISOString().slice(0, 7)
      if (!acc[month]) {
        acc[month] = { count: 0, riskScores: [] }
      }
      acc[month].count++
      
      const riskScore = this.riskLevelToScore(record.risk_level)
      if (riskScore > 0) acc[month].riskScores.push(riskScore)
      
      return acc
    }, {})

    return Object.entries(monthlyData).map(([month, data]: [string, any]) => ({
      month,
      record_count: data.count,
      avg_risk_score: data.riskScores.length > 0 
        ? data.riskScores.reduce((a: number, b: number) => a + b, 0) / data.riskScores.length 
        : 0
    }))
  }

  private riskLevelToScore(riskLevel?: string): number {
    switch (riskLevel) {
      case 'critical': return 4
      case 'high': return 3
      case 'medium': return 2
      case 'low': return 1
      default: return 0
    }
  }

  private generateRecommendations(records: any[]): any[] {
    const recommendations = []

    const highRiskRecords = records.filter(r => r.risk_level === 'high' || r.risk_level === 'critical')

    if (highRiskRecords.length > 0) {
      recommendations.push({
        type: 'urgent',
        message: 'You have recent high-risk health records. Please consult with your ASHA worker.',
        priority: 'high'
      })
    }

    recommendations.push(
      {
        type: 'preventive',
        message: 'Schedule regular health check-ups with your ASHA worker.',
        priority: 'medium'
      },
      {
        type: 'lifestyle',
        message: 'Maintain a balanced diet and regular exercise routine.',
        priority: 'low'
      },
      {
        type: 'monitoring',
        message: 'Keep track of your vital signs and symptoms.',
        priority: 'medium'
      }
    )

    return recommendations
  }
}

export const healthRecordsService = new HealthRecordsService()