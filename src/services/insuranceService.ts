import { supabase } from '../lib/supabase'
import type { InsurancePolicy } from '../lib/supabase'

export interface InsuranceProduct {
  id: string
  name: string
  description: string
  premium_monthly: number
  coverage_amount: number
  features: string[]
  eligibility: any
}

export interface EnrollmentData {
  product_id: string
  coverage_period_months: number
  family_members?: any[]
}

class InsuranceService {
  getInsuranceProducts(): InsuranceProduct[] {
    return [
      {
        id: 'basic_health',
        name: 'Basic Health Cover',
        description: 'Essential health coverage for individuals and families',
        premium_monthly: 50,
        coverage_amount: 5000,
        features: [
          'Hospitalization coverage',
          'Day care procedures',
          'Ambulance charges',
          'Pre-hospitalization expenses'
        ],
        eligibility: {
          min_age: 18,
          max_age: 65,
          family_size: 1
        }
      },
      {
        id: 'family_protection',
        name: 'Family Protection Plan',
        description: 'Comprehensive coverage for entire family',
        premium_monthly: 120,
        coverage_amount: 15000,
        features: [
          'Family coverage (up to 4 members)',
          'Maternity benefits',
          'Child care coverage',
          'Pre-existing conditions after waiting period'
        ],
        eligibility: {
          min_age: 18,
          max_age: 65,
          family_size: 4
        }
      },
      {
        id: 'critical_care',
        name: 'Critical Care Insurance',
        description: 'Coverage for critical illnesses and major surgeries',
        premium_monthly: 200,
        coverage_amount: 25000,
        features: [
          'Critical illness cover',
          'Cancer treatment',
          'Heart surgery coverage',
          'Organ transplant coverage'
        ],
        eligibility: {
          min_age: 21,
          max_age: 60,
          family_size: 1
        }
      },
      {
        id: 'women_child',
        name: 'Women & Child Care',
        description: 'Specialized coverage for women and children',
        premium_monthly: 80,
        coverage_amount: 10000,
        features: [
          'Maternity coverage',
          'Child vaccination',
          'Women-specific health issues',
          'Newborn coverage'
        ],
        eligibility: {
          min_age: 18,
          max_age: 45,
          family_size: 3
        }
      }
    ]
  }

  async enrollInInsurance(enrollmentData: EnrollmentData): Promise<string | null> {
    try {
      const userData = localStorage.getItem('user_data')
      if (!userData) return null

      const user = JSON.parse(userData)
      const product = this.getInsuranceProducts().find(p => p.id === enrollmentData.product_id)
      if (!product) return null

      // Calculate premium and dates
      const totalPremium = product.premium_monthly * enrollmentData.coverage_period_months
      const startDate = new Date()
      const endDate = new Date()
      endDate.setMonth(endDate.getMonth() + enrollmentData.coverage_period_months)

      // Generate policy
      const policyId = crypto.randomUUID()
      const policyNumber = `ASS${Date.now().toString().slice(-8)}`

      const policy = {
        id: policyId,
        citizen_id: user.id,
        policy_type: enrollmentData.product_id,
        policy_number: policyNumber,
        premium_amount: totalPremium,
        coverage_amount: product.coverage_amount,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        status: 'active',
        claims: [],
        created_at: new Date().toISOString()
      }

      // Save to localStorage
      const policies = JSON.parse(localStorage.getItem('insurance_policies') || '[]')
      policies.push(policy)
      localStorage.setItem('insurance_policies', JSON.stringify(policies))

      return policyId
    } catch (error) {
      console.error('Insurance enrollment failed:', error)
      return null
    }
  }

  async getUserPolicies(userId: string): Promise<InsurancePolicy[]> {
    try {
      const policies = JSON.parse(localStorage.getItem('insurance_policies') || '[]')
      return policies.filter((policy: any) => policy.citizen_id === userId)
    } catch (error) {
      console.error('User policies fetch failed:', error)
      return []
    }
  }

  async fileClaim(policyId: string, claimData: any): Promise<boolean> {
    try {
      const policies = JSON.parse(localStorage.getItem('insurance_policies') || '[]')
      const policyIndex = policies.findIndex((p: any) => p.id === policyId)

      if (policyIndex !== -1) {
        const claimId = crypto.randomUUID()
        const claimNumber = `CLM${Date.now().toString().slice(-8)}`

        const newClaim = {
          claim_id: claimId,
          claim_number: claimNumber,
          claim_type: claimData.claim_type,
          claim_amount: claimData.claim_amount,
          incident_description: claimData.incident_description,
          incident_date: claimData.incident_date,
          documents: claimData.documents || [],
          status: 'submitted',
          submitted_date: new Date().toISOString(),
          estimated_processing_days: 7
        }

        policies[policyIndex].claims = policies[policyIndex].claims || []
        policies[policyIndex].claims.push(newClaim)
        localStorage.setItem('insurance_policies', JSON.stringify(policies))
        return true
      }

      return false
    } catch (error) {
      console.error('Claim filing failed:', error)
      return false
    }
  }

  calculatePremium(productId: string, age: number, familySize: number, coveragePeriod: number): any {
    const product = this.getInsuranceProducts().find(p => p.id === productId)
    if (!product) return null

    let basePremium = product.premium_monthly

    // Age factor
    let ageFactor = 1.0
    if (age > 45) ageFactor = 1.2
    else if (age > 35) ageFactor = 1.1

    // Family size factor
    let familyFactor = 1.0
    if (familySize > 1) {
      familyFactor = 0.9 + (familySize * 0.15)
    }

    const monthlyPremium = basePremium * ageFactor * familyFactor
    let totalPremium = monthlyPremium * coveragePeriod

    // Discount for longer terms
    if (coveragePeriod >= 12) {
      totalPremium *= 0.9 // 10% discount
    }

    return {
      product_name: product.name,
      base_premium: basePremium,
      monthly_premium: Math.round(monthlyPremium),
      total_premium: Math.round(totalPremium),
      coverage_amount: product.coverage_amount,
      coverage_period_months: coveragePeriod,
      factors: { ageFactor, familyFactor },
      savings: Math.round((basePremium * coveragePeriod) - totalPremium)
    }
  }
}

export const insuranceService = new InsuranceService()