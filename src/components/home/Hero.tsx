import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Play, Heart, Users, Shield } from 'lucide-react';

const Hero = () => {
  return (
    <section className="relative bg-gradient-to-br from-blue-900 via-blue-800 to-teal-700 text-white overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-black bg-opacity-20">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 rounded-full bg-white transform -translate-x-1/2 -translate-y-1/2"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 rounded-full bg-white transform translate-x-1/2 translate-y-1/2"></div>
        </div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Content */}
          <div className="space-y-8">
            {/* Badge */}
            <div className="inline-flex items-center px-4 py-2 bg-white bg-opacity-10 rounded-full backdrop-blur-sm">
              <Heart className="h-4 w-4 mr-2 text-red-400" />
              <span className="text-sm font-medium">Revolutionizing Rural Healthcare</span>
            </div>

            {/* Heading */}
            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight">
                <span className="text-white">Apna Swasthya</span>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-200 to-teal-200 block">
                  Saathi
                </span>
              </h1>
              <p className="text-xl text-blue-100 leading-relaxed">
                From diagnosis to care, from schemes to insurance - all in one seamless platform. 
                Empowering India's ASHA workers and rural communities.
              </p>
            </div>

            {/* Tagline */}
            <div className="flex items-center space-x-2 text-lg font-medium">
              <span className="px-3 py-1 bg-red-500 rounded-md">Diagnose</span>
              <ArrowRight className="h-5 w-5" />
              <span className="px-3 py-1 bg-green-500 rounded-md">Link</span>
              <ArrowRight className="h-5 w-5" />
              <span className="px-3 py-1 bg-blue-500 rounded-md">Insure</span>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                to="/citizen-login"
                className="inline-flex items-center px-8 py-4 bg-white text-blue-900 rounded-xl font-semibold hover:bg-gray-100 transform hover:scale-105 transition-all duration-200 shadow-xl"
              >
                <Users className="h-5 w-5 mr-3" />
                Start as Citizen
                <ArrowRight className="h-5 w-5 ml-3" />
              </Link>
              <Link
                to="/asha-login"
                className="inline-flex items-center px-8 py-4 border-2 border-white text-white rounded-xl font-semibold hover:bg-white hover:text-blue-900 transition-all duration-200"
              >
                <Shield className="h-5 w-5 mr-3" />
                ASHA Portal
              </Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-6 pt-8">
              <div className="text-center">
                <div className="text-2xl font-bold text-white">1M+</div>
                <div className="text-sm text-blue-200">ASHA Workers</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">10M+</div>
                <div className="text-sm text-blue-200">Families Served</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">90%</div>
                <div className="text-sm text-blue-200">Faster Care</div>
              </div>
            </div>
          </div>

          {/* Visual */}
          <div className="relative">
            <div className="relative z-10">
              <img
                src="https://i.ibb.co/Qj8xnvWf/ddd.jpg"
                alt="Healthcare Worker"
                className="rounded-2xl shadow-2xl"
              />
              {/* Floating Cards */}
              <div className="absolute -top-4 -left-4 bg-white p-4 rounded-xl shadow-lg">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-gray-700">AI Diagnosis Active</span>
                </div>
              </div>
              <div className="absolute -bottom-4 -right-4 bg-white p-4 rounded-xl shadow-lg">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">₹50</div>
                  <div className="text-xs text-gray-500">Insurance Premium</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;