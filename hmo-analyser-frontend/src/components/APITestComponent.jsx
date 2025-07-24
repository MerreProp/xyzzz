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
import PropertyMap from './pages/Map';
import PropertyMapComponent from './components/MapComponent';
import APITestComponent from './components/APITestComponent'; // ← Add this import
import './App.css';

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
      <Router>
        <div className="App">
          <Layout>
            <Routes>
              <Route path="/" element={<Homepage />} />
              <Route path="/analyze" element={<Analyze />} />
              <Route path="/history" element={<History />} />
              <Route path="/advertisers" element={<Advertisers />} />
              <Route path="/advertiser/:advertiserName" element={<AdvertiserDetail />} />
              <Route path="/property/:id" element={<PropertyDetail />} />
              <Route path="/test-phase1" element={<TestPhase1 />} />
              <Route path="/test-phase2" element={<TestPhase2 />} />
              <Route path="/map" element={<PropertyMap />} />
              <Route path="/api-test" element={<APITestComponent />} /> {/* ← Add this route */}
            </Routes>
          </Layout>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;