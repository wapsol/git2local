#!/bin/bash

# Test script for speech query API
# Usage: ./test_speech_queries.sh

API_URL="http://localhost:8000/api/query"

echo "Testing Speech-to-Text Odoo Query API"
echo "======================================"
echo ""

# Check if server is running
echo "1. Checking server health..."
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

# Test queries
declare -a queries=(
    "show my tickets"
    "my open tickets"
    "my closed tickets"
    "show high priority tickets"
    "urgent tickets"
    "my tickets this week"
    "show all tickets today"
    "tickets for euroblaze"
    "my open tickets last 7 days"
    "show 10 tickets"
)

echo "2. Testing query patterns..."
echo ""

for query in "${queries[@]}"
do
    echo "Query: '$query'"
    echo "--------------------"
    curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$query\"}" | python3 -m json.tool | head -20
    echo ""
    echo ""
done

echo "Testing complete!"
echo ""
echo "To test manually:"
echo "  curl -X POST $API_URL -H 'Content-Type: application/json' -d '{\"query\": \"show my open tickets\"}'"
