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
      const userData = localStorage.getItem('user_data')
      if (!userData) return null

      const user = JSON.parse(userData)
      const alertId = crypto.randomUUID()

      const alert = {
        id: alertId,
        citizen_id: user.id,
        alert_type: alertData.alert_type,
        severity: alertData.severity,
        description: alertData.description,
        location: alertData.location,
        status: 'active',
        created_at: new Date().toISOString()
      }

      // Save to localStorage
      const alerts = JSON.parse(localStorage.getItem('emergency_alerts') || '[]')
      alerts.push(alert)
      localStorage.setItem('emergency_alerts', JSON.stringify(alerts))

      // Simulate ASHA notification
      setTimeout(() => {
        console.log('ASHA workers notified about emergency alert:', alertId)
      }, 1000)

      return alertId
    } catch (error) {
      console.error('Emergency alert creation failed:', error)
      return null
    }
  }

  async getUserAlerts(userId: string): Promise<EmergencyAlert[]> {
    try {
      const alerts = JSON.parse(localStorage.getItem('emergency_alerts') || '[]')
      return alerts.filter((alert: any) => alert.citizen_id === userId)
    } catch (error) {
      console.error('User alerts fetch failed:', error)
      return []
    }
  }

  async respondToAlert(alertId: string, responseMessage?: string): Promise<boolean> {
    try {
      const alerts = JSON.parse(localStorage.getItem('emergency_alerts') || '[]')
      const alertIndex = alerts.findIndex((alert: any) => alert.id === alertId)
      
      if (alertIndex !== -1) {
        alerts[alertIndex].status = 'responding'
        alerts[alertIndex].response_time = new Date().toISOString()
        localStorage.setItem('emergency_alerts', JSON.stringify(alerts))
        return true
      }
      
      return false
    } catch (error) {
      console.error('Alert response failed:', error)
      return false
    }
  }

  async resolveAlert(alertId: string, resolutionNotes?: string): Promise<boolean> {
    try {
      const alerts = JSON.parse(localStorage.getItem('emergency_alerts') || '[]')
      const alertIndex = alerts.findIndex((alert: any) => alert.id === alertId)
      
      if (alertIndex !== -1) {
        alerts[alertIndex].status = 'resolved'
        alerts[alertIndex].resolution_time = new Date().toISOString()
        localStorage.setItem('emergency_alerts', JSON.stringify(alerts))
        return true
      }
      
      return false
    } catch (error) {
      console.error('Alert resolution failed:', error)
      return false
    }
  }

  async getAshaAlerts(ashaUserId: string): Promise<EmergencyAlert[]> {
    try {
      const alerts = JSON.parse(localStorage.getItem('emergency_alerts') || '[]')
      // For demo, return all active alerts
      return alerts.filter((alert: any) => alert.status === 'active')
    } catch (error) {
      console.error('ASHA alerts fetch failed:', error)
      return []
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