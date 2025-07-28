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
  async searchFacilities(params: FacilitySearchParams): Promise<HealthcareFacility[]> {
    try {
      let query = supabase.from('healthcare_facilities').select('*')

      if (params.type && params.type !== 'all') {
        query = query.eq('type', params.type)
      }

      if (params.district) {
        query = query.eq('district', params.district)
      }

      if (params.bsky_only) {
        query = query.eq('bsky_empanelled', true)
      }

      query = query.order('rating', { ascending: false }).limit(20)

      const { data: facilities, error } = await query

      if (error) {
        console.error('Facility search failed:', error)
        return []
      }

      return facilities || []
    } catch (error) {
      console.error('Facility search failed:', error)
      return []
    }
  }

  async getNearbyFacilities(userId: string): Promise<HealthcareFacility[]> {
    try {
      // Get user's district
      const { data: user } = await supabase
        .from('users')
        .select('district')
        .eq('id', userId)
        .single()

      if (!user?.district) return []

      const { data: facilities, error } = await supabase
        .from('healthcare_facilities')
        .select('*')
        .eq('district', user.district)
        .order('bsky_empanelled', { ascending: false })
        .order('rating', { ascending: false })
        .limit(10)

      if (error) {
        console.error('Nearby facilities fetch failed:', error)
        return []
      }

      return facilities || []
    } catch (error) {
      console.error('Nearby facilities fetch failed:', error)
      return []
    }
  }

  async getFacilityDetails(facilityId: string): Promise<HealthcareFacility | null> {
    try {
      const { data: facility, error } = await supabase
        .from('healthcare_facilities')
        .select('*')
        .eq('id', facilityId)
        .single()

      if (error) {
        console.error('Facility details fetch failed:', error)
        return null
      }

      return facility
    } catch (error) {
      console.error('Facility details fetch failed:', error)
      return null
    }
  }

  async getEmergencyFacilities(location?: { latitude: number; longitude: number }): Promise<HealthcareFacility[]> {
    try {
      let query = supabase
        .from('healthcare_facilities')
        .select('*')
        .or('type.eq.hospital,services.cs.{"emergency"}')
        .order('bsky_empanelled', { ascending: false })
        .limit(10)

      const { data: facilities, error } = await query

      if (error) {
        console.error('Emergency facilities fetch failed:', error)
        return []
      }

      return facilities || []
    } catch (error) {
      console.error('Emergency facilities fetch failed:', error)
      return []
    }
  }

  async addFacility(facilityData: Partial<HealthcareFacility>): Promise<boolean> {
    try {
      const { error } = await supabase
        .from('healthcare_facilities')
        .insert([facilityData])

      if (error) {
        console.error('Facility addition failed:', error)
        return false
      }

      return true
    } catch (error) {
      console.error('Facility addition failed:', error)
      return false
    }
  }
}

export const facilityService = new FacilityService()