import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import Home from './pages/Home';
import AshaLogin from './pages/AshaLogin';
import AshaDashboard from './pages/AshaDashboard';
import CitizenDashboard from './pages/CitizenDashboard';
import CitizenLogin from './components/citizen/CitizenLogin';
import AboutUs from './pages/AboutUs';
import Services from './pages/Services';
import Contact from './pages/Contact';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <Header />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/asha-login" element={<AshaLogin />} />
            <Route path="/asha-dashboard" element={<AshaDashboard />} />
            <Route path="/citizen-login" element={<CitizenLogin />} />
            <Route path="/citizen" element={<CitizenDashboard />} />
            <Route path="/about" element={<AboutUs />} />
            <Route path="/services" element={<Services />} />
            <Route path="/contact" element={<Contact />} />
          </Routes>
        </main>
        <Footer />
        <Toaster position="top-right" />
      </div>
    </Router>
  );
}

export default App;