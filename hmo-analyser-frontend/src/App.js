import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Homepage from './pages/Homepage';
import Analyze from './pages/Analyze';
import History from './pages/History';
import PropertyDetail from './pages/PropertyDetail';
import Advertisers from './pages/Advertisers';
import AdvertiserDetail from './pages/AdvertiserDetail';
import TestPhase1 from './pages/TestPhase1';
import TestPhase2 from './pages/TestPhase2';
import Layout from './components/Layout';
import Map from './components/Map'; // ← This is correct
import ContactBook from './pages/ContactBook'
import './App.css';
import { AuthProvider  } from './components/AuthContext';
import AuthWrapper from './components/AuthWrapper'
import CityAnalysisPageV2 from './pages/CityAnalysis';
import IndividualCityAnalysis from './pages/IndividualCityAnalysis';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AuthWrapper>
          <Router>
            <div className="App">
              <Layout>
                <Routes>
                  <Route path="/" element={<Homepage />} />
                  <Route path="/analyze" element={<Analyze />} />
                  <Route path="/history" element={<History />} />
                  <Route path="/cityanalysis" element={<CityAnalysisPageV2 />} />
                  <Route path="/cityanalysis/:cityName" element={<IndividualCityAnalysis />} />
                  <Route path="/advertisers" element={<Advertisers />} />
                  <Route path="/advertiser/:advertiserName" element={<AdvertiserDetail />} />
                  <Route path="/property/:id" element={<PropertyDetail />} />
                  <Route path="/test-phase1" element={<TestPhase1 />} />
                  <Route path="/test-phase2" element={<TestPhase2 />} />
                  <Route path="/map" element={<Map />} /> {/* ← CHANGED: Use Map instead of PropertyMap */}
                  <Route path="/contactbook" element={<ContactBook />} />
                </Routes>
              </Layout>
            </div>
          </Router>
        </AuthWrapper>    
       </AuthProvider>   
    </QueryClientProvider>
  );
}

export default App;