#!/bin/bash
# test_hmo_api.sh - Quick test of HMO Registry API endpoints

echo "🧪 Testing HMO Registry API endpoints..."

BASE_URL="http://localhost:8001"

echo ""
echo "1️⃣ Testing available cities:"
curl -s "${BASE_URL}/api/hmo-registry/cities" | jq .

echo ""
echo "2️⃣ Testing Oxford statistics:"
curl -s "${BASE_URL}/api/hmo-registry/cities/oxford/statistics" | jq .

echo ""
echo "3️⃣ Testing Oxford data (first 3 records):"
curl -s "${BASE_URL}/api/hmo-registry/cities/oxford?enable_geocoding=false" | jq '.data[0:3]'

echo ""
echo "4️⃣ Testing legacy endpoints (backward compatibility):"
curl -s "${BASE_URL}/api/oxford-hmo/statistics" | jq .

echo ""
echo "✅ API testing complete!"