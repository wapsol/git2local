#!/bin/bash
#
# Start HTTPS server for Engineering Activity Reports
#
# This script starts a local HTTPS server to serve EAR reports at https://localhost.ear
#
# Usage:
#   sudo ./start_ear_server.sh          # Start on port 443 (requires sudo)
#   ./start_ear_server.sh 8443          # Start on port 8443 (no sudo required)
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default port
PORT="${1:-443}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  EAR Reports HTTPS Server${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running from correct directory
if [ ! -f "serve_reports.py" ]; then
    echo -e "${RED}Error: Must run from git2local directory${NC}"
    exit 1
fi

# Check if localhost.ear is in /etc/hosts
if ! grep -q "localhost.ear" /etc/hosts; then
    echo -e "${YELLOW}Warning: localhost.ear not found in /etc/hosts${NC}"
    echo ""
    echo "To add it, run this command:"
    echo -e "${GREEN}  sudo sh -c \"echo '127.0.0.1 localhost.ear' >> /etc/hosts\"${NC}"
    echo ""
    echo "Or manually add this line to /etc/hosts:"
    echo "  127.0.0.1 localhost.ear"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for SSL certificates
if [ ! -f ".ssl/cert.pem" ] || [ ! -f ".ssl/key.pem" ]; then
    echo -e "${RED}Error: SSL certificates not found!${NC}"
    echo ""
    echo "Generating SSL certificates..."
    mkdir -p .ssl
    cd .ssl
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
        -subj "/CN=localhost.ear/O=Git2Local/C=US"
    cd ..
    echo -e "${GREEN}SSL certificates generated successfully!${NC}"
    echo ""
fi

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}Error: Port $PORT is already in use${NC}"
    echo ""
    echo "Kill the process using port $PORT or choose a different port:"
    echo "  ./start_ear_server.sh 8443"
    exit 1
fi

# Display access information
echo -e "${GREEN}Starting HTTPS server...${NC}"
echo ""
if [ "$PORT" -eq 443 ]; then
    echo -e "Access your reports at: ${GREEN}https://localhost.ear${NC}"
else
    echo -e "Access your reports at: ${GREEN}https://localhost.ear:$PORT${NC}"
fi
echo ""
echo -e "${YELLOW}Note: Your browser will show a security warning for the self-signed certificate.${NC}"
echo -e "${YELLOW}      This is normal. Click 'Advanced' and 'Proceed to localhost.ear' to continue.${NC}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
if [ "$PORT" -eq 443 ]; then
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Error: Port 443 requires sudo privileges${NC}"
        echo ""
        echo "Run with sudo:"
        echo -e "  ${GREEN}sudo ./start_ear_server.sh${NC}"
        echo ""
        echo "Or use a non-privileged port:"
        echo -e "  ${GREEN}./start_ear_server.sh 8443${NC}"
        exit 1
    fi
fi

python3 serve_reports.py "$PORT"
