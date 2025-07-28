import { supabase } from '../lib/supabase'
import type { EmergencyAlert } from '../lib/supabase'

export interface CreateAlertData {
  alert_type: string
  severity: string
  description?: string
  location?: any
}

class EmergencyService {
  async createAlert(alertData: CreateAlertData): Promise<string | null> {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return null

      // Get citizen ID
      const { data: citizen } = await supabase
        .from('citizens')
        .select('id')
        .eq('user_id', user.id)
        .single()

      if (!citizen) return null

      const { data: alert, error } = await supabase
        .from('emergency_alerts')
        .insert([{
          citizen_id: citizen.id,
          alert_type: alertData.alert_type,
          severity: alertData.severity,
          description: alertData.description,
          location: alertData.location,
          status: 'active'
        }])
        .select()
        .single()

      if (error) {
        console.error('Emergency alert creation failed:', error)
        return null
      }

      // Notify nearby ASHA workers
      await this.notifyNearbyAshaWorkers(alert.id, user.id)

      return alert.id
    } catch (error) {
      console.error('Emergency alert creation failed:', error)
      return null
    }
  }

  async getUserAlerts(userId: string): Promise<EmergencyAlert[]> {
    try {
      const { data: citizen } = await supabase
        .from('citizens')
        .select('id')
        .eq('user_id', userId)
        .single()

      if (!citizen) return []

      const { data: alerts, error } = await supabase
        .from('emergency_alerts')
        .select(`
          *,
          asha_workers!emergency_alerts_responder_id_fkey (
            asha_id,
            users!asha_workers_user_id_fkey (full_name)
          )
        `)
        .eq('citizen_id', citizen.id)
        .order('created_at', { ascending: false })
        .limit(50)

      if (error) {
        console.error('User alerts fetch failed:', error)
        return []
      }

      return alerts || []
    } catch (error) {
      console.error('User alerts fetch failed:', error)
      return []
    }
  }

  async respondToAlert(alertId: string, responseMessage?: string): Promise<boolean> {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return false

      // Get ASHA worker ID
      const { data: asha } = await supabase
        .from('asha_workers')
        .select('id')
        .eq('user_id', user.id)
        .single()

      if (!asha) return false

      const { error } = await supabase
        .from('emergency_alerts')
        .update({
          responder_id: asha.id,
          response_time: new Date().toISOString(),
          status: 'responding'
        })
        .eq('id', alertId)
        .eq('status', 'active')

      if (error) {
        console.error('Alert response failed:', error)
        return false
      }

      return true
    } catch (error) {
      console.error('Alert response failed:', error)
      return false
    }
  }

  async resolveAlert(alertId: string, resolutionNotes?: string): Promise<boolean> {
    try {
      const { error } = await supabase
        .from('emergency_alerts')
        .update({
          status: 'resolved',
          resolution_time: new Date().toISOString()
        })
        .eq('id', alertId)

      if (error) {
        console.error('Alert resolution failed:', error)
        return false
      }

      return true
    } catch (error) {
      console.error('Alert resolution failed:', error)
      return false
    }
  }

  async getAshaAlerts(ashaUserId: string): Promise<EmergencyAlert[]> {
    try {
      // Get ASHA worker data
      const { data: asha } = await supabase
        .from('asha_workers')
        .select('assigned_villages')
        .eq('user_id', ashaUserId)
        .single()

      if (!asha) return []

      // Get alerts in assigned villages
      const { data: alerts, error } = await supabase
        .from('emergency_alerts')
        .select(`
          *,
          citizens!emergency_alerts_citizen_id_fkey (
            users!citizens_user_id_fkey (full_name, phone, village)
          )
        `)
        .in('status', ['active', 'responding'])
        .order('created_at', { ascending: false })
        .limit(50)

      if (error) {
        console.error('ASHA alerts fetch failed:', error)
        return []
      }

      // Filter by assigned villages
      const filteredAlerts = alerts?.filter(alert => {
        const village = alert.citizens?.users?.village
        return village && asha.assigned_villages.includes(village)
      })

      return filteredAlerts || []
    } catch (error) {
      console.error('ASHA alerts fetch failed:', error)
      return []
    }
  }

  private async notifyNearbyAshaWorkers(alertId: string, citizenUserId: string): Promise<void> {
    try {
      // Get citizen's village
      const { data: user } = await supabase
        .from('users')
        .select('village')
        .eq('id', citizenUserId)
        .single()

      if (!user?.village) return

      // Find ASHA workers in the same village
      const { data: ashaWorkers } = await supabase
        .from('asha_workers')
        .select(`
          id,
          users!asha_workers_user_id_fkey (full_name, phone)
        `)
        .contains('assigned_villages', [user.village])

      // In a real implementation, send SMS/push notifications here
      console.log(`Notifying ${ashaWorkers?.length || 0} ASHA workers about emergency alert ${alertId}`)
    } catch (error) {
      console.error('ASHA notification failed:', error)
    }
  }

  getEmergencyContacts() {
    return [
      {
        name: 'Emergency Ambulance',
        number: '108',
        description: 'Free 24/7 ambulance service',
        type: 'ambulance'
      },
      {
        name: 'Police Emergency',
        number: '100',
        description: 'Police emergency services',
        type: 'police'
      },
      {
        name: 'Fire Emergency',
        number: '101',
        description: 'Fire and rescue services',
        type: 'fire'
      },
      {
        name: 'Women Helpline',
        number: '1091',
        description: '24x7 helpline for women in distress',
        type: 'women_safety'
      }
    ]
  }
}

export const emergencyService = new EmergencyService()