import { supabase } from '../lib/supabase'
import type { User } from '../lib/supabase'

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  user_type: 'asha' | 'citizen'
  full_name: string
  phone?: string
  district?: string
  block?: string
  village?: string
  abha_id?: string
}

export interface AuthResponse {
  success: boolean
  user?: User
  error?: string
  access_token?: string
}

class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      // First authenticate with Supabase Auth
      const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
        email: credentials.email,
        password: credentials.password
      })

      if (authError) {
        return { success: false, error: authError.message }
      }

      // Get user profile from our users table
      const { data: userData, error: userError } = await supabase
        .from('users')
        .select('*')
        .eq('email', credentials.email)
        .eq('is_active', true)
        .single()

      if (userError || !userData) {
        return { success: false, error: 'User profile not found' }
      }

      return {
        success: true,
        user: userData,
        access_token: authData.session?.access_token
      }
    } catch (error) {
      return { success: false, error: 'Login failed' }
    }
  }

  async demoLogin(userType: 'asha' | 'citizen'): Promise<AuthResponse> {
    const demoCredentials = {
      asha: { email: 'asha@demo.com', password: 'demo123' },
      citizen: { email: 'citizen@demo.com', password: 'demo123' }
    }

    return this.login(demoCredentials[userType])
  }

  async register(data: RegisterData): Promise<AuthResponse> {
    try {
      // Create auth user
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: data.email,
        password: data.password
      })

      if (authError) {
        return { success: false, error: authError.message }
      }

      // Create user profile
      const { data: userData, error: userError } = await supabase
        .from('users')
        .insert([{
          id: authData.user?.id,
          email: data.email,
          user_type: data.user_type,
          full_name: data.full_name,
          phone: data.phone,
          district: data.district,
          block: data.block,
          village: data.village,
          abha_id: data.abha_id
        }])
        .select()
        .single()

      if (userError) {
        return { success: false, error: 'Failed to create user profile' }
      }

      // Create type-specific profile
      if (data.user_type === 'asha') {
        await supabase.from('asha_workers').insert([{
          user_id: userData.id,
          asha_id: `ASHA${Date.now()}`,
          training_status: 'pending',
          performance_score: 0,
          assigned_villages: data.village ? [data.village] : []
        }])
      } else if (data.user_type === 'citizen') {
        await supabase.from('citizens').insert([{
          user_id: userData.id
        }])
      }

      return {
        success: true,
        user: userData,
        access_token: authData.session?.access_token
      }
    } catch (error) {
      return { success: false, error: 'Registration failed' }
    }
  }

  async logout(): Promise<void> {
    await supabase.auth.signOut()
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_data')
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      
      if (!user) return null

      const { data: userData } = await supabase
        .from('users')
        .select('*')
        .eq('id', user.id)
        .single()

      return userData
    } catch (error) {
      return null
    }
  }

  async refreshToken(): Promise<string | null> {
    try {
      const { data, error } = await supabase.auth.refreshSession()
      if (error) return null
      return data.session?.access_token || null
    } catch (error) {
      return null
    }
  }
}

export const authService = new AuthService()