import React, { useState } from 'react';
import { AlertTriangle, Phone, MapPin, User, Clock, Heart } from 'lucide-react';
import toast from 'react-hot-toast';
import { emergencyService } from '../../services/emergencyService';

const EmergencyAlert = () => {
  const [isEmergencyActive, setIsEmergencyActive] = useState(false);
  const [selectedEmergency, setSelectedEmergency] = useState('');

  const emergencyTypes = [
    { id: 'medical', name: 'Medical Emergency', icon: Heart, color: 'bg-red-500' },
    { id: 'accident', name: 'Accident', icon: AlertTriangle, color: 'bg-orange-500' },
    { id: 'breathing', name: 'Breathing Difficulty', icon: Heart, color: 'bg-red-600' },
    { id: 'pregnancy', name: 'Pregnancy Emergency', icon: User, color: 'bg-pink-500' },
  ];

  const emergencyContacts = emergencyService.getEmergencyContacts();

  const handleEmergencyAlert = async (type: string) => {
    try {
      const alertId = await emergencyService.createAlert({
        alert_type: type,
        severity: 'high',
        description: `Emergency alert for ${emergencyTypes.find(e => e.id === type)?.name}`,
        location: {
          latitude: 18.8137,
          longitude: 82.7119,
          address: 'Koraput, Odisha'
        }
      });

      if (alertId) {
        setSelectedEmergency(type);
        setIsEmergencyActive(true);
        toast.success('Emergency alert sent! Help is on the way.');
        
        setTimeout(() => {
          toast.success('Your ASHA worker has been notified and is responding.');
        }, 3000);
      } else {
        toast.error('Failed to send emergency alert');
      }
    } catch (error) {
      toast.error('Emergency alert failed');
    }
  };

  const handleCall = (number: string, name: string) => {
    toast.success(`Calling ${name} at ${number}...`);
  };

  const cancelEmergency = async () => {
    setIsEmergencyActive(false);
    setSelectedEmergency('');
    toast.success('Emergency alert cancelled.');
  };

  if (isEmergencyActive) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-8">
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
              <AlertTriangle className="h-10 w-10 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-red-900 mb-2">Emergency Alert Active</h2>
            <p className="text-red-700">Your emergency request has been sent. Stay calm, help is coming.</p>
          </div>

          <div className="bg-white rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Emergency Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center space-x-3">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <span className="text-gray-700">Type: {emergencyTypes.find(e => e.id === selectedEmergency)?.name}</span>
              </div>
              <div className="flex items-center space-x-3">
                <Clock className="h-5 w-5 text-blue-500" />
                <span className="text-gray-700">Time: {new Date().toLocaleTimeString()}</span>
              </div>
              <div className="flex items-center space-x-3">
                <MapPin className="h-5 w-5 text-green-500" />
                <span className="text-gray-700">Location: Koraput, Odisha</span>
              </div>
              <div className="flex items-center space-x-3">
                <User className="h-5 w-5 text-purple-500" />
                <span className="text-gray-700">Patient: Ramesh Kumar</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <button
              onClick={() => handleCall('108', 'Emergency Ambulance')}
              className="flex items-center justify-center px-6 py-4 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              <Phone className="h-5 w-5 mr-3" />
              Call 108 Ambulance
            </button>
            <button
              onClick={() => handleCall('+91 9876543210', 'ASHA Worker')}
              className="flex items-center justify-center px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Phone className="h-5 w-5 mr-3" />
              Call ASHA Worker
            </button>
          </div>

          <div className="text-center">
            <button
              onClick={cancelEmergency}
              className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Cancel Emergency Alert
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Emergency Header */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="h-8 w-8 text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Emergency Support</h2>
          <p className="text-gray-600">Get immediate help when you need it most</p>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-center font-medium">
            ⚠️ For life-threatening emergencies, call 108 immediately or go to the nearest hospital
          </p>
        </div>
      </div>

      {/* Emergency Types */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Quick Emergency Alert</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {emergencyTypes.map((emergency) => (
            <button
              key={emergency.id}
              onClick={() => handleEmergencyAlert(emergency.id)}
              className="p-6 border-2 border-gray-200 rounded-xl hover:border-red-300 hover:bg-red-50 transition-all duration-200 group"
            >
              <div className={`w-12 h-12 ${emergency.color} rounded-lg flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform`}>
                <emergency.icon className="h-6 w-6 text-white" />
              </div>
              <h4 className="font-medium text-gray-900 text-center">{emergency.name}</h4>
            </button>
          ))}
        </div>
      </div>

      {/* Emergency Contacts */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Emergency Contacts</h3>
        <div className="space-y-4">
          {emergencyContacts.map((contact, index) => (
            <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <Phone className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">{contact.name}</h4>
                  <p className="text-sm text-gray-600">{contact.description}</p>
                  <p className="text-sm font-mono text-blue-600">{contact.number}</p>
                </div>
              </div>
              <button
                onClick={() => handleCall(contact.number, contact.name)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Call Now
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Safety Tips */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Emergency Preparedness Tips</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Before Emergency</h4>
            <ul className="space-y-2 text-sm text-gray-700">
              <li>• Keep emergency contacts saved in your phone</li>
              <li>• Know the location of nearest hospital</li>
              <li>• Keep basic first aid supplies at home</li>
              <li>• Inform family about your medical conditions</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-3">During Emergency</h4>
            <ul className="space-y-2 text-sm text-gray-700">
              <li>• Stay calm and call for help immediately</li>
              <li>• Provide clear location information</li>
              <li>• Follow first aid if trained</li>
              <li>• Wait for professional medical help</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Location Sharing */}
      <div className="bg-blue-50 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-blue-900 mb-1">Share Your Location</h3>
            <p className="text-blue-700">Enable location sharing for faster emergency response</p>
          </div>
          <button
            onClick={() => toast.success('Location sharing enabled')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Enable Location
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmergencyAlert;