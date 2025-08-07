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
      // For demo purposes, use localStorage-based authentication
      const demoUsers = {
        'asha@demo.com': {
          id: '550e8400-e29b-41d4-a716-446655440001',
          email: 'asha@demo.com',
          user_type: 'asha' as const,
          full_name: 'Priya Patel',
          phone: '+91 9876543210',
          district: 'Koraput',
          block: 'Koraput',
          village: 'Kendrapara',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        'citizen@demo.com': {
          id: '550e8400-e29b-41d4-a716-446655440002',
          email: 'citizen@demo.com',
          user_type: 'citizen' as const,
          full_name: 'Ramesh Kumar',
          phone: '+91 9876543211',
          abha_id: '12-3456-7890-1234',
          district: 'Koraput',
          block: 'Koraput',
          village: 'Bhadrak',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      }

      const demoPasswords = {
        'asha@demo.com': 'demo123',
        'citizen@demo.com': 'demo123'
      }

      const user = demoUsers[credentials.email as keyof typeof demoUsers]
      const validPassword = demoPasswords[credentials.email as keyof typeof demoPasswords]

      if (!user || credentials.password !== validPassword) {
        return { success: false, error: 'Invalid credentials' }
      }

      // Generate mock token
      const access_token = `demo_token_${user.id}_${Date.now()}`

      return {
        success: true,
        user,
        access_token
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
      // For demo purposes, just return success
      const newUser: User = {
        id: crypto.randomUUID(),
        email: data.email,
        user_type: data.user_type,
        full_name: data.full_name,
        phone: data.phone,
        district: data.district,
        block: data.block,
        village: data.village,
        abha_id: data.abha_id,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }

      return {
        success: true,
        user: newUser,
        access_token: `demo_token_${newUser.id}_${Date.now()}`
      }
    } catch (error) {
      return { success: false, error: 'Registration failed' }
    }
  }

  async logout(): Promise<void> {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_data')
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const userData = localStorage.getItem('user_data')
      return userData ? JSON.parse(userData) : null
    } catch (error) {
      return null
    }
  }

  async refreshToken(): Promise<string | null> {
    try {
      const userData = localStorage.getItem('user_data')
      if (userData) {
        const user = JSON.parse(userData)
        return `demo_token_${user.id}_${Date.now()}`
      }
      return null
    } catch (error) {
      return null
    }
  }
}

export const authService = new AuthService()