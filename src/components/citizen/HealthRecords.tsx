import React, { useState } from 'react';
import { FileText, Download, Share, Eye, Calendar, User, Stethoscope } from 'lucide-react';
import toast from 'react-hot-toast';
import { healthRecordsService } from '../../services/healthRecordsService';
import type { HealthRecord } from '../../lib/supabase';

const HealthRecords = () => {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [healthRecords, setHealthRecords] = useState<HealthRecord[]>([]);
  const [healthSummary, setHealthSummary] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Load health records on component mount
  React.useEffect(() => {
    loadHealthData();
  }, [selectedCategory]);

  const loadHealthData = async () => {
    setIsLoading(true);
    try {
      const userData = localStorage.getItem('user_data');
      if (userData) {
        const user = JSON.parse(userData);
        
        // Load records with filters
        const filters = {
          record_type: selectedCategory,
          limit: 50
        };
        const records = await healthRecordsService.getHealthRecords(user.id, filters);
        setHealthRecords(records);

        // Load summary
        const summary = await healthRecordsService.getHealthSummary(user.id);
        setHealthSummary(summary);
      }
    } catch (error) {
      toast.error('Failed to load health records');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const userData = localStorage.getItem('user_data');
      if (userData) {
        const user = JSON.parse(userData);
        const exportData = await healthRecordsService.exportHealthRecords(user.id);
        
        // Create and download file
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `health-records-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        toast.success('Health records exported successfully');
      }
    } catch (error) {
      toast.error('Export failed');
    }
  };

  const categories = [
    { id: 'all', name: 'All Records' },
    { id: 'diagnoses', name: 'Diagnoses' },
    { id: 'prescriptions', name: 'Prescriptions' },
    { id: 'tests', name: 'Test Reports' },
    { id: 'visits', name: 'Doctor Visits' },
  ];

  const healthRecords = [
    {
      id: 1,
      type: 'diagnosis',
      title: 'Anemia Screening',
      provider: 'ASHA - Priya Patel',
      date: '2024-01-15',
      status: 'High Risk',
      details: 'Hemoglobin: 7.2 g/dL - Requires immediate attention',
      actions: ['View', 'Download', 'Share']
    },
    {
      id: 2,
      type: 'prescription',
      title: 'Iron Supplement Prescription',
      provider: 'Dr. Rajesh Kumar, PHC Koraput',
      date: '2024-01-16',
      status: 'Active',
      details: 'Iron + Folic Acid tablets - 1 tablet daily for 3 months',
      actions: ['View', 'Download']
    },
    {
      id: 3,
      type: 'test',
      title: 'Complete Blood Count',
      provider: 'District Hospital Lab',
      date: '2024-01-18',
      status: 'Normal',
      details: 'All parameters within normal range',
      actions: ['View', 'Download', 'Share']
    },
    {
      id: 4,
      type: 'visit',
      title: 'Follow-up Consultation',
      provider: 'Dr. Sunita Singh, CHC Jeypore',
      date: '2024-01-20',
      status: 'Completed',
      details: 'Patient showing improvement, continue medication',
      actions: ['View', 'Download']
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'High Risk': return 'bg-red-100 text-red-800';
      case 'Active': return 'bg-blue-100 text-blue-800';
      case 'Normal': return 'bg-green-100 text-green-800';
      case 'Completed': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'diagnosis': return Stethoscope;
      case 'prescription': return FileText;
      case 'test': return FileText;
      case 'visit': return User;
      default: return FileText;
    }
  };

  const handleAction = (action: string, recordTitle: string) => {
    toast.success(`${action} ${recordTitle}...`);
  };

  const filteredRecords = selectedCategory === 'all' 
    ? healthRecords 
    : healthRecords.filter(record => {
        switch (selectedCategory) {
          case 'diagnoses': return record.type === 'diagnosis';
          case 'prescriptions': return record.type === 'prescription';
          case 'tests': return record.type === 'test';
          case 'visits': return record.type === 'visit';
          default: return true;
        }
      });

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">My Health Records</h2>
            <p className="text-gray-600">Secure access to your complete health history</p>
          </div>
          <div className="mt-4 md:mt-0">
            <button
              onClick={() => toast.success('Downloading complete health summary...')}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Download className="h-4 w-4 mr-2" />
              Download Summary
            </button>
          </div>
        </div>

        {/* ABHA Integration Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
              <FileText className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-blue-900">ABHA Linked Records</h3>
              <p className="text-sm text-blue-700">Your records are securely stored and linked to your ABHA ID: 12-3456-7890-1234</p>
            </div>
          </div>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2">
          {categories.map(category => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedCategory === category.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {category.name}
            </button>
          ))}
        </div>
      </div>

      {/* Health Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <Stethoscope className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Latest Diagnosis</h3>
              <p className="text-sm text-gray-600">Anemia - High Risk</p>
            </div>
          </div>
          <p className="text-sm text-gray-700">Hemoglobin level: 7.2 g/dL</p>
          <p className="text-xs text-gray-500 mt-2">Screened on Jan 15, 2024</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Active Prescriptions</h3>
              <p className="text-sm text-gray-600">2 medications</p>
            </div>
          </div>
          <p className="text-sm text-gray-700">Iron + Folic Acid</p>
          <p className="text-xs text-gray-500 mt-2">Daily for 3 months</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Calendar className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Next Appointment</h3>
              <p className="text-sm text-gray-600">Follow-up visit</p>
            </div>
          </div>
          <p className="text-sm text-gray-700">Dr. Sunita Singh</p>
          <p className="text-xs text-gray-500 mt-2">Feb 15, 2024</p>
        </div>
      </div>

      {/* Records List */}
      <div className="bg-white rounded-xl shadow-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Detailed Records</h3>
        </div>

        <div className="divide-y divide-gray-200">
          {filteredRecords.map((record) => {
            const IconComponent = getTypeIcon(record.type);
            return (
              <div key={record.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <IconComponent className="h-6 w-6 text-gray-600" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-lg font-medium text-gray-900">{record.title}</h4>
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(record.status)}`}>
                        {record.status}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-1">{record.provider}</p>
                    <p className="text-sm text-gray-700 mb-2">{record.details}</p>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center text-sm text-gray-500">
                        <Calendar className="h-4 w-4 mr-1" />
                        {record.date}
                      </div>
                      
                      <div className="flex space-x-2">
                        {record.actions.map((action) => (
                          <button
                            key={action}
                            onClick={() => handleAction(action, record.title)}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            {action}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Privacy Notice */}
      <div className="bg-gray-50 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Privacy & Security</h3>
        <p className="text-sm text-gray-600 mb-4">
          Your health records are encrypted and stored securely in compliance with ABDM standards. 
          You have full control over who can access your health information.
        </p>
        <div className="flex items-center space-x-4">
          <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            Manage Permissions
          </button>
          <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            Download Data
          </button>
          <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            Privacy Settings
          </button>
        </div>
      </div>
    </div>
  );
};

export default HealthRecords;