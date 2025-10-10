#!/usr/bin/env python3
"""
HTTPS Server for Engineering Activity Reports
Serves EAR reports at https://localhost.ear

Usage:
    sudo python3 serve_reports.py [port]

Default port: 443 (requires sudo)
Alternative: Use port 8443 (no sudo required)

Example:
    sudo python3 serve_reports.py         # Runs on port 443
    python3 serve_reports.py 8443         # Runs on port 8443 (no sudo)
"""

import http.server
import ssl
import os
import sys
from pathlib import Path

class EARRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for EAR reports."""

    def __init__(self, *args, **kwargs):
        # Serve from the reports directory
        super().__init__(*args, directory="reports", **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        # If requesting root, redirect to latest report
        if self.path == '/':
            latest_report = self.get_latest_report()
            if latest_report:
                self.path = f'/{latest_report}'

        return super().do_GET()

    def get_latest_report(self):
        """Find the most recent EAR report."""
        reports_dir = Path('reports')
        if not reports_dir.exists():
            return None

        # Find all EAR HTML files
        ear_files = sorted(
            reports_dir.glob('EAR_*.html'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if ear_files:
            return ear_files[0].name
        return None

    def end_headers(self):
        """Add CORS headers for API access."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()


def main():
    # Determine port
    port = 443
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}", file=sys.stderr)
            sys.exit(1)

    # Check if SSL certificates exist
    cert_file = Path('.ssl/cert.pem')
    key_file = Path('.ssl/key.pem')

    if not cert_file.exists() or not key_file.exists():
        print("Error: SSL certificates not found!", file=sys.stderr)
        print("Run this command to generate them:", file=sys.stderr)
        print("  mkdir -p .ssl && cd .ssl && \\", file=sys.stderr)
        print("  openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \\", file=sys.stderr)
        print('    -subj "/CN=localhost.ear/O=Git2Local/C=US"', file=sys.stderr)
        sys.exit(1)

    # Check if reports directory exists
    if not Path('reports').exists():
        print("Error: 'reports' directory not found!", file=sys.stderr)
        sys.exit(1)

    # Create HTTPS server
    server_address = ('0.0.0.0', port)
    httpd = http.server.HTTPServer(server_address, EARRequestHandler)

    # Wrap with SSL
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(str(cert_file), str(key_file))
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    print(f"Starting HTTPS server on port {port}...", file=sys.stderr)
    print(f"Access your reports at: https://localhost.ear{':' + str(port) if port != 443 else ''}", file=sys.stderr)
    print("Press Ctrl+C to stop the server", file=sys.stderr)
    print(f"\nServing reports from: {Path('reports').absolute()}", file=sys.stderr)

    # Find and display latest report
    handler = EARRequestHandler
    latest = Path('reports')
    ear_files = sorted(latest.glob('EAR_*.html'), key=lambda p: p.stat().st_mtime, reverse=True)
    if ear_files:
        print(f"Latest report: {ear_files[0].name}", file=sys.stderr)

    print("\nNote: Your browser will show a security warning for the self-signed certificate.", file=sys.stderr)
    print("      This is normal. Click 'Advanced' and 'Proceed to localhost.ear' to continue.\n", file=sys.stderr)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.", file=sys.stderr)
        httpd.shutdown()


if __name__ == '__main__':
    main()
