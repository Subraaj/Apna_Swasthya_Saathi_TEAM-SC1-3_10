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
  async getHealthRecords(userId: string, filters?: any): Promise<HealthRecord[]> {
    try {
      const { data: citizen } = await supabase
        .from('citizens')
        .select('id')
        .eq('user_id', userId)
        .single()

      if (!citizen) return []

      let query = supabase
        .from('health_records')
        .select(`
          *,
          ai_diagnoses (*)
        `)
        .eq('citizen_id', citizen.id)

      if (filters?.record_type && filters.record_type !== 'all') {
        query = query.eq('record_type', filters.record_type)
      }

      if (filters?.start_date) {
        query = query.gte('created_at', filters.start_date)
      }

      if (filters?.end_date) {
        query = query.lte('created_at', filters.end_date)
      }

      query = query.order('created_at', { ascending: false })

      if (filters?.limit) {
        query = query.limit(filters.limit)
      }

      const { data: records, error } = await query

      if (error) {
        console.error('Health records fetch failed:', error)
        return []
      }

      return records || []
    } catch (error) {
      console.error('Health records fetch failed:', error)
      return []
    }
  }

  async getHealthSummary(userId: string): Promise<HealthSummary | null> {
    try {
      const { data: citizen } = await supabase
        .from('citizens')
        .select(`
          *,
          users!citizens_user_id_fkey (*)
        `)
        .eq('user_id', userId)
        .single()

      if (!citizen) return null

      // Get recent records (last 30 days)
      const thirtyDaysAgo = new Date()
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

      const { data: recentRecords } = await supabase
        .from('health_records')
        .select('record_type, created_at')
        .eq('citizen_id', citizen.id)
        .gte('created_at', thirtyDaysAgo.toISOString())

      // Get latest vital signs
      const { data: latestVitals } = await supabase
        .from('health_records')
        .select('vital_signs, created_at')
        .eq('citizen_id', citizen.id)
        .not('vital_signs', 'is', null)
        .order('created_at', { ascending: false })
        .limit(1)

      // Get risk distribution
      const { data: riskData } = await supabase
        .from('health_records')
        .select('risk_level')
        .eq('citizen_id', citizen.id)
        .not('risk_level', 'is', null)

      const riskDistribution = riskData?.reduce((acc: any, record) => {
        acc[record.risk_level] = (acc[record.risk_level] || 0) + 1
        return acc
      }, {})

      // Get recent medications
      const { data: medications } = await supabase
        .from('health_records')
        .select('medications, created_at')
        .eq('citizen_id', citizen.id)
        .not('medications', 'is', null)
        .order('created_at', { ascending: false })
        .limit(5)

      const summary: HealthSummary = {
        patient_info: {
          name: citizen.users?.full_name,
          age: this.calculateAge(citizen.date_of_birth),
          gender: citizen.gender,
          blood_group: citizen.blood_group,
          abha_id: citizen.users?.abha_id
        },
        recent_activity: {
          records_last_30_days: recentRecords?.length || 0,
          record_types: this.groupRecordTypes(recentRecords || [])
        },
        latest_vitals: latestVitals?.[0] || null,
        risk_assessment: {
          distribution: Object.entries(riskDistribution || {}).map(([level, count]) => ({
            risk_level: level,
            count
          })),
          current_risk: await this.getCurrentRiskLevel(citizen.id)
        },
        medications: medications || [],
        health_trends: await this.getHealthTrends(citizen.id),
        recommendations: this.generateRecommendations(riskDistribution)
      }

      return summary
    } catch (error) {
      console.error('Health summary generation failed:', error)
      return null
    }
  }

  async createHealthRecord(userId: string, recordData: Partial<HealthRecord>): Promise<string | null> {
    try {
      const { data: citizen } = await supabase
        .from('citizens')
        .select('id')
        .eq('user_id', userId)
        .single()

      if (!citizen) return null

      const { data: record, error } = await supabase
        .from('health_records')
        .insert([{
          citizen_id: citizen.id,
          ...recordData
        }])
        .select()
        .single()

      if (error) {
        console.error('Health record creation failed:', error)
        return null
      }

      return record.id
    } catch (error) {
      console.error('Health record creation failed:', error)
      return null
    }
  }

  async updateHealthRecord(recordId: string, userId: string, updateData: Partial<HealthRecord>): Promise<boolean> {
    try {
      // Verify ownership
      const { data: citizen } = await supabase
        .from('citizens')
        .select('id')
        .eq('user_id', userId)
        .single()

      if (!citizen) return false

      const { error } = await supabase
        .from('health_records')
        .update(updateData)
        .eq('id', recordId)
        .eq('citizen_id', citizen.id)

      if (error) {
        console.error('Health record update failed:', error)
        return false
      }

      return true
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

  private async getCurrentRiskLevel(citizenId: string): Promise<string> {
    try {
      const { data: record } = await supabase
        .from('health_records')
        .select('risk_level')
        .eq('citizen_id', citizenId)
        .not('risk_level', 'is', null)
        .order('created_at', { ascending: false })
        .limit(1)
        .single()

      return record?.risk_level || 'unknown'
    } catch (error) {
      return 'unknown'
    }
  }

  private async getHealthTrends(citizenId: string): Promise<any[]> {
    try {
      // Get trends over last 6 months
      const sixMonthsAgo = new Date()
      sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6)

      const { data: records } = await supabase
        .from('health_records')
        .select('created_at, risk_level')
        .eq('citizen_id', citizenId)
        .gte('created_at', sixMonthsAgo.toISOString())

      // Group by month
      const monthlyData = records?.reduce((acc: any, record) => {
        const month = new Date(record.created_at).toISOString().slice(0, 7)
        if (!acc[month]) {
          acc[month] = { count: 0, riskScores: [] }
        }
        acc[month].count++
        
        // Convert risk level to score
        const riskScore = this.riskLevelToScore(record.risk_level)
        if (riskScore > 0) acc[month].riskScores.push(riskScore)
        
        return acc
      }, {})

      return Object.entries(monthlyData || {}).map(([month, data]: [string, any]) => ({
        month,
        record_count: data.count,
        avg_risk_score: data.riskScores.length > 0 
          ? data.riskScores.reduce((a: number, b: number) => a + b, 0) / data.riskScores.length 
          : 0
      }))
    } catch (error) {
      console.error('Health trends calculation failed:', error)
      return []
    }
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

  private generateRecommendations(riskDistribution?: any): any[] {
    const recommendations = []

    if (riskDistribution?.high > 0 || riskDistribution?.critical > 0) {
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