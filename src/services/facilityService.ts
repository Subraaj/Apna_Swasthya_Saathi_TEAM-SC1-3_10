import { supabase } from '../lib/supabase'
import type { HealthcareFacility } from '../lib/supabase'

export interface FacilitySearchParams {
  type?: string
  district?: string
  bsky_only?: boolean
  latitude?: number
  longitude?: number
  radius_km?: number
}

class FacilityService {
  private getDemoFacilities(): HealthcareFacility[] {
    return [
      {
        id: '1',
        name: 'PHC Koraput',
        type: 'phc',
        address: 'Main Road, Koraput, Odisha',
        district: 'Koraput',
        block: 'Koraput',
        coordinates: { lat: 18.8137, lng: 82.7119 },
        contact_info: { phone: '+91 9876543210', email: 'phc.koraput@gov.in' },
        services: ['General Medicine', 'Maternal Care', 'Vaccination', 'Basic Diagnostics'],
        bsky_empanelled: true,
        operating_hours: { '24x7': true },
        rating: 4.2,
        created_at: new Date().toISOString()
      },
      {
        id: '2',
        name: 'District Hospital Koraput',
        type: 'hospital',
        address: 'Hospital Road, Koraput, Odisha',
        district: 'Koraput',
        block: 'Koraput',
        coordinates: { lat: 18.8137, lng: 82.7119 },
        contact_info: { phone: '+91 9876543211', emergency: '+91 9876543215' },
        services: ['Emergency Care', 'Surgery', 'ICU', 'Specialist Care'],
        bsky_empanelled: true,
        operating_hours: { '24x7': true },
        rating: 4.5,
        created_at: new Date().toISOString()
      },
      {
        id: '3',
        name: 'CHC Jeypore',
        type: 'chc',
        address: 'Jeypore, Koraput District, Odisha',
        district: 'Koraput',
        block: 'Jeypore',
        coordinates: { lat: 18.8564, lng: 82.5742 },
        contact_info: { phone: '+91 9876543212' },
        services: ['Specialist Care', 'Lab Services', 'X-Ray'],
        bsky_empanelled: true,
        operating_hours: { open: '6:00', close: '22:00' },
        rating: 4.0,
        created_at: new Date().toISOString()
      },
      {
        id: '4',
        name: 'Apollo Clinic Koraput',
        type: 'private',
        address: 'Market Street, Koraput, Odisha',
        district: 'Koraput',
        coordinates: { lat: 18.8137, lng: 82.7119 },
        contact_info: { phone: '+91 9876543213' },
        services: ['General Medicine', 'Cardiology', 'Pediatrics', 'Diagnostics'],
        bsky_empanelled: false,
        operating_hours: { open: '9:00', close: '21:00' },
        rating: 4.8,
        created_at: new Date().toISOString()
      }
    ]
  }

  async searchFacilities(params: FacilitySearchParams): Promise<HealthcareFacility[]> {
    try {
      let facilities = this.getDemoFacilities()

      if (params.type && params.type !== 'all') {
        facilities = facilities.filter(f => f.type === params.type)
      }

      if (params.district) {
        facilities = facilities.filter(f => f.district.toLowerCase().includes(params.district!.toLowerCase()))
      }

      if (params.bsky_only) {
        facilities = facilities.filter(f => f.bsky_empanelled)
      }

      return facilities
    } catch (error) {
      console.error('Facility search failed:', error)
      return []
    }
  }

  async getNearbyFacilities(userId: string): Promise<HealthcareFacility[]> {
    try {
      const userData = localStorage.getItem('user_data')
      if (!userData) return []

      const user = JSON.parse(userData)
      const facilities = this.getDemoFacilities()

      // Filter by user's district
      return facilities.filter(f => f.district === user.district)
    } catch (error) {
      console.error('Nearby facilities fetch failed:', error)
      return []
    }
  }

  async getFacilityDetails(facilityId: string): Promise<HealthcareFacility | null> {
    try {
      const facilities = this.getDemoFacilities()
      return facilities.find(f => f.id === facilityId) || null
    } catch (error) {
      console.error('Facility details fetch failed:', error)
      return null
    }
  }

  async getEmergencyFacilities(location?: { latitude: number; longitude: number }): Promise<HealthcareFacility[]> {
    try {
      const facilities = this.getDemoFacilities()
      return facilities.filter(f => 
        f.type === 'hospital' || 
        f.services?.includes('Emergency Care') ||
        f.operating_hours?.['24x7']
      )
    } catch (error) {
      console.error('Emergency facilities fetch failed:', error)
      return []
    }
  }

  async addFacility(facilityData: Partial<HealthcareFacility>): Promise<boolean> {
    try {
      // For demo, just return success
      return true
    } catch (error) {
      console.error('Facility addition failed:', error)
      return false
    }
  }
}

export const facilityService = new FacilityService()