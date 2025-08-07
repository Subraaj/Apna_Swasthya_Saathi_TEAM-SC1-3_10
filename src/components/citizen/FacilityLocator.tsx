import React, { useState } from 'react';
import { MapPin, Navigation, Phone, Clock, Star } from 'lucide-react';
import toast from 'react-hot-toast';
import { facilityService } from '../../services/facilityService';

const FacilityLocator = () => {
  const [selectedType, setSelectedType] = useState('all');
  const [searchLocation, setSearchLocation] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const facilityTypes = [
    { id: 'all', name: 'All Facilities' },
    { id: 'phc', name: 'Primary Health Centers' },
    { id: 'chc', name: 'Community Health Centers' },
    { id: 'hospital', name: 'Government Hospitals' },
    { id: 'private', name: 'Private Clinics' },
  ];

  const nearbyFacilities = [
    {
      id: 1,
      name: 'PHC Koraput',
      type: 'Primary Health Center',
      distance: '2.3 km',
      address: 'Main Road, Koraput, Odisha',
      phone: '+91 9876543210',
      hours: '24/7',
      rating: 4.2,
      services: ['General Medicine', 'Maternal Care', 'Vaccination'],
      bskyEnabled: true
    },
    {
      id: 2,
      name: 'District Hospital Koraput',
      type: 'Government Hospital',
      distance: '5.7 km',
      address: 'Hospital Road, Koraput, Odisha',
      phone: '+91 9876543211',
      hours: '24/7',
      rating: 4.5,
      services: ['Emergency Care', 'Surgery', 'Specialist Consultation'],
      bskyEnabled: true
    },
    {
      id: 3,
      name: 'CHC Jeypore',
      type: 'Community Health Center',
      distance: '8.1 km',
      address: 'Jeypore, Koraput District, Odisha',
      phone: '+91 9876543212',
      hours: '6 AM - 10 PM',
      rating: 4.0,
      services: ['Specialist Care', 'Lab Services', 'X-Ray'],
      bskyEnabled: true
    },
    {
      id: 4,
      name: 'Apollo Clinic',
      type: 'Private Clinic',
      distance: '3.2 km',
      address: 'Market Street, Koraput, Odisha',
      phone: '+91 9876543213',
      hours: '9 AM - 9 PM',
      rating: 4.8,
      services: ['General Medicine', 'Cardiology', 'Pediatrics'],
      bskyEnabled: false
    }
  ];

  const handleGetDirections = (facilityName: string) => {
    toast.success(`Opening directions to ${facilityName}...`);
  };

  const handleCallFacility = (phone: string) => {
    toast.success(`Calling ${phone}...`);
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          toast.success('Location detected! Updating nearby facilities...');
        },
        (error) => {
          toast.error('Could not get your location. Please enable location services.');
        }
      );
    } else {
      toast.error('Geolocation is not supported by this browser.');
    }
  };

  const filteredFacilities = selectedType === 'all' 
    ? nearbyFacilities 
    : nearbyFacilities.filter(facility => {
        switch (selectedType) {
          case 'phc': return facility.type.includes('Primary');
          case 'chc': return facility.type.includes('Community');
          case 'hospital': return facility.type.includes('Hospital');
          case 'private': return facility.type.includes('Private');
          default: return true;
        }
      });

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Find Healthcare Facilities</h2>
        
        {/* Search and Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="relative">
            <input
              type="text"
              placeholder="Enter your location..."
              value={searchLocation}
              onChange={(e) => setSearchLocation(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <MapPin className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
          </div>
          
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {facilityTypes.map(type => (
              <option key={type.id} value={type.id}>{type.name}</option>
            ))}
          </select>
          
          <button
            onClick={getCurrentLocation}
            className="flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Navigation className="h-4 w-4 mr-2" />
            Use My Location
          </button>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">24</div>
            <div className="text-sm text-blue-800">Nearby Facilities</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">18</div>
            <div className="text-sm text-green-800">BSKY Enabled</div>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">8</div>
            <div className="text-sm text-purple-800">24/7 Services</div>
          </div>
          <div className="text-center p-3 bg-teal-50 rounded-lg">
            <div className="text-2xl font-bold text-teal-600">4.3</div>
            <div className="text-sm text-teal-800">Avg Rating</div>
          </div>
        </div>
      </div>

      {/* Facilities List */}
      <div className="space-y-4">
        {filteredFacilities.map((facility) => (
          <div key={facility.id} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              {/* Facility Info */}
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-xl font-semibold text-gray-900">{facility.name}</h3>
                  {facility.bskyEnabled && (
                    <span className="inline-flex items-center px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                      BSKY Enabled
                    </span>
                  )}
                </div>
                
                <p className="text-sm text-gray-600 mb-2">{facility.type}</p>
                <p className="text-sm text-gray-700 mb-2">{facility.address}</p>
                
                <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                  <div className="flex items-center space-x-1">
                    <MapPin className="h-4 w-4" />
                    <span>{facility.distance}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="h-4 w-4" />
                    <span>{facility.hours}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Star className="h-4 w-4 text-yellow-500" />
                    <span>{facility.rating}</span>
                  </div>
                </div>

                {/* Services */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {facility.services.map((service, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-md"
                    >
                      {service}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col space-y-2 lg:ml-6">
                <button
                  onClick={() => handleGetDirections(facility.name)}
                  className="flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Navigation className="h-4 w-4 mr-2" />
                  Directions
                </button>
                <button
                  onClick={() => handleCallFacility(facility.phone)}
                  className="flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Phone className="h-4 w-4 mr-2" />
                  Call Now
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Emergency Banner */}
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-red-900 mb-1">Medical Emergency?</h3>
            <p className="text-red-700">Call 108 for free ambulance service or contact your ASHA worker immediately.</p>
          </div>
          <div className="flex space-x-3">
            <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
              Call 108
            </button>
            <button className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors">
              Alert ASHA
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FacilityLocator;