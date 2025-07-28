import { supabase } from '../lib/supabase'

export interface SymptomAnalysis {
  symptoms: string[]
  vital_signs?: any
  patient_history?: any
}

export interface AIResponse {
  success: boolean
  analysis?: {
    condition: string
    confidence_score: number
    risk_level: string
    recommendations: string[]
    requires_immediate_attention: boolean
  }
  error?: string
}

export interface VoiceAnalysis {
  success: boolean
  transcribed_text?: string
  analysis?: any
  error?: string
}

class AIService {
  private geminiApiKey = 'AIzaSyA17TYUA-SKvSUhVPh9EtKZWWyPyVQOp08'

  async analyzeSymptoms(data: SymptomAnalysis): Promise<AIResponse> {
    try {
      const symptomsText = Array.isArray(data.symptoms) ? data.symptoms.join(', ') : data.symptoms
      
      const prompt = `
        You are a medical AI assistant for rural healthcare in India. Analyze these symptoms:
        
        Symptoms: ${symptomsText}
        Vital Signs: ${data.vital_signs ? JSON.stringify(data.vital_signs) : 'Not provided'}
        
        Provide analysis in this JSON format:
        {
          "condition": "most likely condition",
          "confidence_score": 0.85,
          "risk_level": "low/medium/high/critical",
          "recommendations": ["recommendation 1", "recommendation 2"],
          "requires_immediate_attention": false
        }
        
        Focus on common conditions in rural India. Be conservative in recommendations.
      `

      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${this.geminiApiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }]
        })
      })

      if (!response.ok) {
        throw new Error('Gemini API request failed')
      }

      const result = await response.json()
      const content = result.candidates[0]?.content?.parts[0]?.text

      let analysis
      try {
        analysis = JSON.parse(content)
      } catch {
        // Fallback if JSON parsing fails
        analysis = {
          condition: 'requires_assessment',
          confidence_score: 0.7,
          risk_level: 'medium',
          recommendations: ['Consult with ASHA worker', 'Monitor symptoms'],
          requires_immediate_attention: false
        }
      }

      // Save analysis to database
      await this.saveAnalysis(data, analysis)

      return { success: true, analysis }
    } catch (error) {
      console.error('AI Analysis failed:', error)
      return {
        success: false,
        error: 'Analysis failed. Please consult your ASHA worker.'
      }
    }
  }

  async processVoiceInput(audioBlob: Blob, language = 'hi'): Promise<VoiceAnalysis> {
    try {
      // Mock voice processing - in production, use speech-to-text service
      const mockTranscriptions = {
        hi: 'मुझे बुखार और सिरदर्द है',
        en: 'I have fever and headache',
        or: 'ମୋର ଜ୍ୱର ଓ ମୁଣ୍ଡବିନ୍ଧା ହେଉଛି'
      }

      const transcribedText = mockTranscriptions[language as keyof typeof mockTranscriptions] || mockTranscriptions.en

      // Extract symptoms from transcribed text
      const symptoms = this.extractSymptomsFromText(transcribedText, language)

      // Analyze symptoms
      const analysis = await this.analyzeSymptoms({ symptoms })

      return {
        success: true,
        transcribed_text: transcribedText,
        analysis: analysis.analysis
      }
    } catch (error) {
      return {
        success: false,
        error: 'Voice processing failed'
      }
    }
  }

  private extractSymptomsFromText(text: string, language: string): string[] {
    const symptomKeywords = {
      hi: {
        'बुखार': 'fever',
        'सिरदर्द': 'headache',
        'खांसी': 'cough',
        'दर्द': 'pain',
        'कमजोर': 'weakness'
      },
      en: {
        'fever': 'fever',
        'headache': 'headache',
        'cough': 'cough',
        'pain': 'pain',
        'weak': 'weakness'
      },
      or: {
        'ଜ୍ୱର': 'fever',
        'ମୁଣ୍ଡବିନ୍ଧା': 'headache',
        'କାଶ': 'cough'
      }
    }

    const keywords = symptomKeywords[language as keyof typeof symptomKeywords] || symptomKeywords.en
    const extractedSymptoms: string[] = []

    Object.entries(keywords).forEach(([keyword, symptom]) => {
      if (text.toLowerCase().includes(keyword.toLowerCase())) {
        extractedSymptoms.push(symptom)
      }
    })

    return extractedSymptoms
  }

  private async saveAnalysis(inputData: SymptomAnalysis, analysis: any): Promise<void> {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      // Get citizen ID
      const { data: citizen } = await supabase
        .from('citizens')
        .select('id')
        .eq('user_id', user.id)
        .single()

      if (!citizen) return

      // Save health record
      const { data: healthRecord } = await supabase
        .from('health_records')
        .insert([{
          citizen_id: citizen.id,
          record_type: 'ai_diagnosis',
          symptoms: inputData.symptoms,
          vital_signs: inputData.vital_signs,
          diagnosis: {
            condition: analysis.condition,
            confidence: analysis.confidence_score,
            ai_analysis: analysis
          },
          risk_level: analysis.risk_level,
          recommendations: analysis.recommendations.join('\n')
        }])
        .select()
        .single()

      // Save AI diagnosis details
      if (healthRecord) {
        await supabase
          .from('ai_diagnoses')
          .insert([{
            health_record_id: healthRecord.id,
            model_used: 'gemini_1.5_flash',
            input_data: inputData,
            prediction_results: analysis,
            confidence_score: analysis.confidence_score,
            processing_time_ms: 1000
          }])
      }
    } catch (error) {
      console.error('Failed to save analysis:', error)
    }
  }

  async getDiagnosisHistory(userId: string): Promise<any[]> {
    try {
      const { data: citizen } = await supabase
        .from('citizens')
        .select('id')
        .eq('user_id', userId)
        .single()

      if (!citizen) return []

      const { data: records } = await supabase
        .from('health_records')
        .select(`
          *,
          ai_diagnoses (*)
        `)
        .eq('citizen_id', citizen.id)
        .order('created_at', { ascending: false })
        .limit(50)

      return records || []
    } catch (error) {
      console.error('Failed to get diagnosis history:', error)
      return []
    }
  }
}

export const aiService = new AIService()