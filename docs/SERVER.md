# EAR Reports HTTPS Server

This document explains how to serve Engineering Activity Reports (EAR) locally at `https://localhost.ear`.

## Quick Start

### Option 1: Using Port 8443 (No sudo required)

```bash
# Start the server on port 8443
./start_ear_server.sh 8443

# Access in browser
https://localhost.ear:8443
```

### Option 2: Using Port 443 (Requires sudo)

```bash
# First, add localhost.ear to /etc/hosts (one-time setup)
sudo sh -c "echo '127.0.0.1 localhost.ear' >> /etc/hosts"

# Start the server on port 443
sudo ./start_ear_server.sh

# Access in browser
https://localhost.ear
```

## Setup Instructions

### 1. Add Custom Domain to /etc/hosts

To use the clean URL `https://localhost.ear` (without port number), add this entry to `/etc/hosts`:

```bash
sudo sh -c "echo '127.0.0.1 localhost.ear' >> /etc/hosts"
```

Or manually edit `/etc/hosts` and add:
```
127.0.0.1 localhost.ear
```

### 2. SSL Certificates

SSL certificates are automatically generated when you first run `start_ear_server.sh`.

If you need to regenerate them manually:

```bash
mkdir -p .ssl
cd .ssl
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
    -subj "/CN=localhost.ear/O=Git2Local/C=US"
cd ..
```

### 3. Start the Server

**Using the convenience script (recommended):**

```bash
# Port 8443 (no sudo required)
./start_ear_server.sh 8443

# Port 443 (requires sudo, cleaner URL)
sudo ./start_ear_server.sh
```

**Using Python directly:**

```bash
# Port 8443
python3 serve_reports.py 8443

# Port 443 (requires sudo)
sudo python3 serve_reports.py
```

## Usage

### Accessing Reports

1. **Start the server** using one of the methods above
2. **Open your browser** and navigate to:
   - `https://localhost.ear:8443` (if using port 8443)
   - `https://localhost.ear` (if using port 443)
3. **Accept the security warning**:
   - Browser will show "Your connection is not private"
   - Click **Advanced**
   - Click **Proceed to localhost.ear (unsafe)**
   - This is normal for self-signed certificates

### Features

- **Automatic latest report**: Visiting the root URL (`/`) automatically serves the most recent EAR report
- **Direct access**: You can also access specific reports by filename:
  - `https://localhost.ear:8443/EAR_2025-10-09.html`
- **Speech interface**: The speech query interface works when the Odoo API server is running
- **CORS enabled**: API requests from the speech interface work correctly

### Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

Or find and kill the process:

```bash
# Find the process
lsof -i :8443  # or :443

# Kill it
kill <PID>
```

## Speech Query Interface

The speech interface requires the Odoo query API server to be running:

```bash
# Set the Odoo password
export ODOO_PASSWORD="your_password"

# Start the API server
python3 odoo_query_server.py
```

Then use the microphone button in the report header to:
- Query Odoo helpdesk tickets by voice
- Filter by priority, status, customer, etc.
- View results in a modal overlay

## Troubleshooting

### Port Already in Use

```
Error: Port 8443 is already in use
```

**Solution**: Either kill the existing process or use a different port:

```bash
lsof -i :8443  # Find the PID
kill <PID>     # Kill the process

# Or use a different port
./start_ear_server.sh 9443
```

### SSL Certificate Warning

This is **normal and expected** for self-signed certificates. Modern browsers require valid SSL certificates signed by a trusted Certificate Authority (CA). Our self-signed certificates are not trusted by default.

**Safe to proceed** because:
- This is a local development server
- You control both the server and the certificate
- No sensitive data is transmitted over the internet

### localhost.ear Not Resolving

If the browser can't find `localhost.ear`:

1. **Check /etc/hosts**:
   ```bash
   grep localhost.ear /etc/hosts
   ```

2. **Add it if missing**:
   ```bash
   sudo sh -c "echo '127.0.0.1 localhost.ear' >> /etc/hosts"
   ```

3. **Clear DNS cache** (macOS):
   ```bash
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   ```

### Can't Access on Port 443

Port 443 requires administrator privileges:

```bash
# Must use sudo
sudo ./start_ear_server.sh

# Or use a non-privileged port instead
./start_ear_server.sh 8443
```

## Files

- `serve_reports.py` - Python HTTPS server script
- `start_ear_server.sh` - Convenience shell script
- `.ssl/cert.pem` - SSL certificate (self-signed)
- `.ssl/key.pem` - SSL private key
- `reports/` - Directory containing EAR HTML reports

## Security Notes

- **Self-signed certificates**: Only for local development. Never use in production.
- **Private key**: Keep `.ssl/key.pem` secure. It's in `.gitignore` by default.
- **HTTPS required**: The speech interface uses Web Speech API which requires HTTPS.
- **CORS enabled**: Server allows cross-origin requests for API functionality.

## Alternative Access Methods

If you don't want to set up the HTTPS server, you can also:

1. **Direct file access**:
   ```
   file:///Users/ashant/git2local/reports/EAR_2025-10-09.html
   ```
   ⚠️ Speech interface won't work (requires HTTPS)

2. **Simple HTTP server** (Python built-in):
   ```bash
   cd reports
   python3 -m http.server 8000
   ```
   Access at: `http://localhost:8000/EAR_2025-10-09.html`

   ⚠️ Speech interface won't work (requires HTTPS)

## Next Steps

1. Generate a report: `./git2local --non-interactive --period=week`
2. Start the HTTPS server: `./start_ear_server.sh 8443`
3. Open browser: `https://localhost.ear:8443`
4. (Optional) Start Odoo API server for speech queries
5. Use the speech interface to query tickets by voice
