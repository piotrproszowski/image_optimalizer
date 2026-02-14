#!/bin/bash
# Integration test script

set -e

echo "🧪 Testing Web Deployment"
echo "========================="
echo

# Start server in background
echo "Starting server..."
cd server
cargo run --release &
SERVER_PID=$!
cd ..

# Wait for server to start
echo "Waiting for server to be ready..."
sleep 5

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:3000/api/health || echo "failed")

if echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    echo "Response: $HEALTH_RESPONSE"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Cleanup
echo "Cleaning up..."
kill $SERVER_PID 2>/dev/null || true

echo
echo "✅ All tests passed!"
