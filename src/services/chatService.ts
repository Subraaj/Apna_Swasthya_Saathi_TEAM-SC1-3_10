import { supabase } from '../lib/supabase'
import { aiService } from './aiService'

export interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: string
  suggestions?: string[]
  actions?: any[]
}

export interface ChatSession {
  id: string
  language: string
  messages: ChatMessage[]
  context: any
  created_at: string
}

class ChatService {
  async startSession(language = 'en', sessionType = 'health_consultation'): Promise<string | null> {
    try {
      const userData = localStorage.getItem('user_data')
      if (!userData) return null

      const user = JSON.parse(userData)
      const sessionId = crypto.randomUUID()

      const sessionData = {
        id: sessionId,
        user_id: user.id,
        session_type: sessionType,
        language,
        messages: [],
        context: {
          user_symptoms: [],
          current_topic: null,
          assessment_stage: 'initial'
        },
        created_at: new Date().toISOString()
      }

      // Save to localStorage
      const sessions = JSON.parse(localStorage.getItem('chat_sessions') || '[]')
      sessions.push(sessionData)
      localStorage.setItem('chat_sessions', JSON.stringify(sessions))

      return sessionId
    } catch (error) {
      console.error('Failed to start chat session:', error)
      return null
    }
  }

  async sendMessage(sessionId: string, message: string, messageType = 'text'): Promise<ChatMessage | null> {
    try {
      const userData = localStorage.getItem('user_data')
      if (!userData) return null

      const user = JSON.parse(userData)

      // Get session
      const sessions = JSON.parse(localStorage.getItem('chat_sessions') || '[]')
      const sessionIndex = sessions.findIndex((s: any) => s.id === sessionId && s.user_id === user.id)
      
      if (sessionIndex === -1) return null

      const session = sessions[sessionIndex]
      
      // Add user message
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        type: 'user',
        content: message,
        timestamp: new Date().toISOString()
      }

      session.messages.push(userMessage)

      // Generate AI response
      const aiResponse = await this.generateAIResponse(message, session, user.id)
      
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        type: 'assistant',
        content: aiResponse.content,
        suggestions: aiResponse.suggestions,
        actions: aiResponse.actions,
        timestamp: new Date().toISOString()
      }

      session.messages.push(assistantMessage)
      session.context = aiResponse.updated_context || session.context
      session.updated_at = new Date().toISOString()

      // Update session
      sessions[sessionIndex] = session
      localStorage.setItem('chat_sessions', JSON.stringify(sessions))

      return assistantMessage
    } catch (error) {
      console.error('Failed to send message:', error)
      return null
    }
  }

  async getSession(sessionId: string): Promise<ChatSession | null> {
    try {
      const userData = localStorage.getItem('user_data')
      if (!userData) return null

      const user = JSON.parse(userData)
      const sessions = JSON.parse(localStorage.getItem('chat_sessions') || '[]')
      
      return sessions.find((s: any) => s.id === sessionId && s.user_id === user.id) || null
    } catch (error) {
      console.error('Failed to get session:', error)
      return null
    }
  }

  async getUserSessions(): Promise<ChatSession[]> {
    try {
      const userData = localStorage.getItem('user_data')
      if (!userData) return []

      const user = JSON.parse(userData)
      const sessions = JSON.parse(localStorage.getItem('chat_sessions') || '[]')
      
      return sessions.filter((s: any) => s.user_id === user.id)
    } catch (error) {
      console.error('Failed to get user sessions:', error)
      return []
    }
  }

  private async generateAIResponse(message: string, sessionData: any, userId: string): Promise<any> {
    try {
      const context = sessionData.context || {}
      const language = sessionData.language || 'en'

      // Check for health-related keywords
      const healthKeywords = this.extractHealthKeywords(message, language)
      
      if (healthKeywords.length > 0) {
        context.user_symptoms = [...(context.user_symptoms || []), ...healthKeywords]
        context.current_topic = 'symptom_assessment'
        
        // Use AI service for symptom analysis
        const analysis = await aiService.analyzeSymptoms({
          symptoms: healthKeywords
        })

        if (analysis.success && analysis.analysis) {
          return {
            content: this.formatHealthResponse(analysis.analysis, language),
            suggestions: this.generateSuggestions(context, language),
            actions: this.generateActions(context, healthKeywords),
            updated_context: context
          }
        }
      }

      // Generate general response using Gemini
      const response = await this.getGeminiResponse(message, context, language)
      
      return {
        content: response,
        suggestions: this.generateSuggestions(context, language),
        actions: this.generateActions(context, healthKeywords),
        updated_context: context
      }
    } catch (error) {
      console.error('AI response generation failed:', error)
      return {
        content: this.getFallbackResponse(sessionData.language),
        suggestions: [],
        actions: [],
        updated_context: sessionData.context
      }
    }
  }

  private extractHealthKeywords(message: string, language: string): string[] {
    const healthKeywords = {
      en: ['fever', 'headache', 'cough', 'pain', 'tired', 'weak', 'dizzy', 'nausea'],
      hi: ['बुखार', 'सिरदर्द', 'खांसी', 'दर्द', 'थकान', 'कमजोर', 'चक्कर', 'उल्टी'],
      or: ['ଜ୍ୱର', 'ମୁଣ୍ଡବିନ୍ଧା', 'କାଶ', 'ଯନ୍ତ୍ରଣା', 'ଦୁର୍ବଳତା']
    }

    const keywords = healthKeywords[language as keyof typeof healthKeywords] || healthKeywords.en
    const found: string[] = []

    keywords.forEach(keyword => {
      if (message.toLowerCase().includes(keyword.toLowerCase())) {
        found.push(keyword)
      }
    })

    return found
  }

  private async getGeminiResponse(message: string, context: any, language: string): Promise<string> {
    try {
      const prompt = `
        You are a helpful AI health assistant for rural India. 
        User message: "${message}"
        Language: ${language}
        Context: ${JSON.stringify(context)}
        
        Provide a helpful, culturally appropriate response in ${language === 'hi' ? 'Hindi' : language === 'or' ? 'Odia' : 'English'}.
        Keep it concise and actionable.
      `

      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${this.geminiApiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }]
        })
      })

      const result = await response.json()
      return result.candidates[0]?.content?.parts[0]?.text || this.getFallbackResponse(language)
    } catch (error) {
      return this.getFallbackResponse(language)
    }
  }

  private formatHealthResponse(analysis: any, language: string): string {
    const responses = {
      en: `Based on your symptoms, I've identified a possible ${analysis.condition} with ${Math.round(analysis.confidence_score * 100)}% confidence. Risk level: ${analysis.risk_level}. 

Recommendations:
${analysis.recommendations.map((r: string) => `• ${r}`).join('\n')}

${analysis.requires_immediate_attention ? '⚠️ Please seek immediate medical attention!' : 'Please consult with your ASHA worker for further guidance.'}`,
      
      hi: `आपके लक्षणों के आधार पर, मैंने ${Math.round(analysis.confidence_score * 100)}% विश्वास के साथ संभावित ${analysis.condition} की पहचान की है। जोखिम स्तर: ${analysis.risk_level}।

सिफारिशें:
${analysis.recommendations.map((r: string) => `• ${r}`).join('\n')}

${analysis.requires_immediate_attention ? '⚠️ कृपया तुरंत चिकित्सा सहायता लें!' : 'कृपया आगे के मार्गदर्शन के लिए अपने ASHA कार्यकर्ता से सलाह लें।'}`
    }

    return responses[language as keyof typeof responses] || responses.en
  }

  private generateSuggestions(context: any, language: string): string[] {
    const suggestions = {
      en: [
        'Tell me about your symptoms',
        'Find nearby healthcare facilities',
        'Check government health schemes',
        'Emergency assistance'
      ],
      hi: [
        'अपने लक्षणों के बारे में बताएं',
        'नजदीकी स्वास्थ्य सुविधाएं खोजें',
        'सरकारी स्वास्थ्य योजनाएं देखें',
        'आपातकालीन सहायता'
      ]
    }

    return suggestions[language as keyof typeof suggestions] || suggestions.en
  }

  private generateActions(context: any, healthKeywords: string[]): any[] {
    const actions = []

    if (healthKeywords.length > 0) {
      actions.push({
        type: 'symptom_analysis',
        label: 'Analyze Symptoms',
        description: 'Get detailed AI analysis'
      })
    }

    actions.push(
      {
        type: 'find_facilities',
        label: 'Find Healthcare',
        description: 'Locate nearby facilities'
      },
      {
        type: 'emergency_alert',
        label: 'Emergency Help',
        description: 'Get immediate assistance'
      }
    )

    return actions
  }

  private getFallbackResponse(language: string): string {
    const responses = {
      en: "I'm here to help with your health concerns. Please feel free to ask about symptoms, healthcare facilities, or government schemes.",
      hi: "मैं आपकी स्वास्थ्य चिंताओं में मदद करने के लिए यहां हूं। कृपया लक्षण, स्वास्थ्य सुविधाओं या सरकारी योजनाओं के बारे में पूछें।",
      or: "ମୁଁ ଆପଣଙ୍କର ସ୍ୱାସ୍ଥ୍ୟ ଚିନ୍ତାରେ ସାହାଯ୍ୟ କରିବା ପାଇଁ ଏଠାରେ ଅଛି।"
    }

    return responses[language as keyof typeof responses] || responses.en
  }
}

export const chatService = new ChatService()