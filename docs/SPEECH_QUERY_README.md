# Speech-to-Text Odoo Query Interface

## Overview

This feature adds voice-controlled natural language querying to the Engineering Activity Report HTML interface. Users can speak queries like "show my open tickets" and get real-time results from the Odoo helpdesk system.

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Browser    │────▶ │  FastAPI     │────▶ │  Odoo API    │
│ (Web Speech) │      │   Server     │      │  (XML-RPC)   │
│    API       │◀─────│ (Parser+     │◀─────│              │
└──────────────┘      │  Query)      │      └──────────────┘
                      └──────────────┘
```

## Components

### 1. Query Parser (`query_parser.py`)

Converts natural language to Odoo domain filters.

**Supported Patterns:**
- `"my tickets"` → User's assigned tickets
- `"my open tickets"` → Open tickets for user
- `"my closed tickets"` → Closed tickets for user
- `"high priority tickets"` → Priority level filters
- `"urgent tickets"` → Urgent priority
- `"tickets for euroblaze"` → Customer filter
- `"tickets this week"` → Time-based filter
- `"show 10 tickets"` → Result limit
- `"all open tickets"` → All users, open state

**Example Usage:**
```python
from query_parser import QueryParser

parser = QueryParser(user_id=2, username="ashant")
domain, options = parser.parse("show my open tickets this week")

# Returns:
# domain = [('user_id', '=', 2), ('close_date', '=', False), ('write_date', '>=', '2025-10-06')]
# options = {'limit': 50, 'order': 'write_date desc', 'fields': [...]}
```

### 2. Odoo API Extension (`odoo_api.py`)

Added `query_tickets()` method for flexible querying:

```python
from odoo_api import OdooAPI

odoo = OdooAPI('https://erp.wapsol.de', 'wapsol', 'user@example.com', 'password')
odoo.authenticate()

# Query with custom domain
tickets = odoo.query_tickets(
    domain=[('user_id', '=', 2), ('priority', '=', '2')],
    limit=20,
    order='write_date desc'
)
```

### 3. FastAPI Backend (`odoo_query_server.py`)

REST API server for processing speech queries.

**Endpoints:**

- `GET /` - API information
- `GET /health` - Health check with Odoo connection status
- `POST /api/query` - Process natural language query
- `GET /api/test-connection` - Test Odoo connectivity

**API Request Example:**
```json
POST http://localhost:8000/api/query
Content-Type: application/json

{
  "query": "show my open tickets"
}
```

**API Response Example:**
```json
{
  "success": true,
  "query": "show my open tickets",
  "query_summary": "Your open tickets (limit: 50)",
  "domain": [["user_id", "=", 2], ["close_date", "=", false]],
  "result_count": 15,
  "tickets": [
    {
      "id": 1234,
      "name": "Fix login bug",
      "user": "Ashant Kumar",
      "customer": "Euroblaze GmbH",
      "project": "Website Maintenance",
      "stage": "In Progress",
      "priority": "1",
      "create_date": "2025-10-01 10:30:00",
      "write_date": "2025-10-08 15:45:00",
      "close_date": false,
      "is_closed": false,
      "description": "Users are unable to login using SSO..."
    }
  ]
}
```

### 4. HTML Interface (To Be Added)

**Features to implement:**
- "Speak" button with microphone icon in header controls
- Web Speech API integration (webkit)
- Results modal/panel displaying query results
- Ticket cards matching existing design
- Real-time query status indicators

**Required CSS additions (add after line 779):**
```css
/* Speech Query Interface */
.speak-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 5px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
}

.speak-button:hover {
    background: rgba(255, 255, 255, 0.3);
}

.speak-button.listening {
    background: #dc3545;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.query-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: none;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.query-modal.active {
    display: flex;
}

.query-panel {
    background: white;
    border-radius: 8px;
    padding: 2rem;
    max-width: 900px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.query-status {
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 5px;
    text-align: center;
}

.query-status.listening {
    background: #fff3cd;
    color: #856404;
}

.query-status.processing {
    background: #d1ecf1;
    color: #0c5460;
}

.query-status.success {
    background: #d4edda;
    color: #155724;
}

.query-status.error {
    background: #f8d7da;
    color: #721c24;
}
```

**Required HTML additions (add in header-controls section after line 610):**
```html
<button class="speak-button" id="speakButton">
    <span id="speakIcon">🎤</span>
    <span id="speakText">Speak</span>
</button>
```

**Required JavaScript additions (add before closing script tag):**
```javascript
// Speech Query Interface
const API_ENDPOINT = 'http://localhost:8000/api/query';
let recognition = null;

// Check for speech recognition support
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
}

const speakButton = document.getElementById('speakButton');
const speakIcon = document.getElementById('speakIcon');
const speakText = document.getElementById('speakText');

if (speakButton && recognition) {
    speakButton.addEventListener('click', function() {
        startSpeechQuery();
    });
} else if (speakButton && !recognition) {
    speakButton.disabled = true;
    speakButton.title = 'Speech recognition not supported in this browser';
    speakIcon.textContent = '🚫';
}

function startSpeechQuery() {
    speakButton.classList.add('listening');
    speakIcon.textContent = '🔴';
    speakText.textContent = 'Listening...';

    recognition.start();
}

recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    console.log('Recognized:', transcript);

    speakButton.classList.remove('listening');
    speakIcon.textContent = '⏳';
    speakText.textContent = 'Processing...';

    processQuery(transcript);
};

recognition.onerror = function(event) {
    console.error('Speech recognition error:', event.error);
    speakButton.classList.remove('listening');
    speakIcon.textContent = '🎤';
    speakText.textContent = 'Speak';

    showQueryStatus('Error: ' + event.error, 'error');
};

recognition.onend = function() {
    speakButton.classList.remove('listening');
    if (speakIcon.textContent !== '⏳') {
        speakIcon.textContent = '🎤';
        speakText.textContent = 'Speak';
    }
};

async function processQuery(queryText) {
    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: queryText })
        });

        const data = await response.json();

        speakIcon.textContent = '🎤';
        speakText.textContent = 'Speak';

        if (data.success) {
            displayQueryResults(data);
        } else {
            showQueryStatus('Error: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Query processing error:', error);
        speakIcon.textContent = '🎤';
        speakText.textContent = 'Speak';
        showQueryStatus('Network error: ' + error.message, 'error');
    }
}

function displayQueryResults(data) {
    // Create modal if not exists
    let modal = document.getElementById('queryModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'queryModal';
        modal.className = 'query-modal';
        modal.innerHTML = `
            <div class="query-panel">
                <h2 style="margin-bottom: 1rem;">Query Results</h2>
                <div id="queryContent"></div>
                <button onclick="document.getElementById('queryModal').classList.remove('active')"
                        style="margin-top: 1rem; padding: 0.5rem 1rem; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    Close
                </button>
            </div>
        `;
        document.body.appendChild(modal);
    }

    const content = document.getElementById('queryContent');
    content.innerHTML = `
        <div class="query-status success">
            <strong>Query:</strong> ${data.query}<br>
            <strong>Results:</strong> ${data.query_summary} - ${data.result_count} ticket(s) found
        </div>
        <div class="cards-grid" style="margin-top: 1rem;">
            ${data.tickets.map(ticket => `
                <div class="activity-card">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span class="activity-type-badge activity-type-ticket">TICKET</span>
                        <span class="badge ${ticket.is_closed ? 'badge-closed' : 'badge-open'}">
                            ${ticket.is_closed ? 'CLOSED' : 'OPEN'}
                        </span>
                    </div>
                    <h5>#${ticket.id} ${ticket.name}</h5>
                    <div class="item-meta">
                        <strong>Customer:</strong> ${ticket.customer}<br>
                        <strong>Project:</strong> ${ticket.project}<br>
                        <strong>Stage:</strong> ${ticket.stage} | <strong>Priority:</strong> ${ticket.priority}
                    </div>
                    ${ticket.description ? `<div class="text-preview">${ticket.description}</div>` : ''}
                </div>
            `).join('')}
        </div>
    `;

    modal.classList.add('active');
}

function showQueryStatus(message, type) {
    const modal = document.getElementById('queryModal') || createQueryModal();
    const content = document.getElementById('queryContent');

    content.innerHTML = `
        <div class="query-status ${type}">
            ${message}
        </div>
    `;

    modal.classList.add('active');

    if (type === 'error') {
        setTimeout(() => modal.classList.remove('active'), 3000);
    }
}
```

## Setup and Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export ODOO_PASSWORD="your_odoo_password"
```

### 3. Start the FastAPI Server

```bash
# Option 1: Direct execution
python odoo_query_server.py

# Option 2: Using uvicorn
ODOO_PASSWORD=your_password uvicorn odoo_query_server:app --reload

# Server starts at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### 4. Generate Report with Speech Interface

The HTML report should already include the speech interface if properly implemented. Simply open the generated report in a browser:

```bash
# Generate report (with or without Odoo data)
./git2local --non-interactive --period=week --include-odoo

# Open report
open reports/EAR_2025-10-09.html
```

### 5. Use Voice Queries

1. Click the "Speak" button (🎤) in the header
2. Speak your query (e.g., "show my open tickets")
3. Results appear in a modal overlay

## Query Examples

| Query | Result |
|-------|--------|
| "show my tickets" | All tickets assigned to you |
| "my open tickets" | Your open tickets |
| "high priority tickets" | Tickets with high or urgent priority |
| "tickets for euroblaze" | Tickets for customer matching "euroblaze" |
| "my tickets this week" | Your tickets updated this week |
| "show 10 tickets" | Limit results to 10 tickets |
| "all open tickets" | All open tickets (not just yours) |
| "urgent tickets today" | Urgent priority tickets updated today |

## Testing

### Test Query Parser

```bash
python query_parser.py
```

### Test API Server

```bash
# Terminal 1: Start server
ODOO_PASSWORD=your_password python odoo_query_server.py

# Terminal 2: Test health endpoint
curl http://localhost:8000/health

# Terminal 3: Test query endpoint
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "show my open tickets"}'
```

### Test in Browser

1. Open browser console (F12)
2. Test speech recognition:
```javascript
const recognition = new webkitSpeechRecognition();
recognition.lang = 'en-US';
recognition.onresult = (event) => console.log(event.results[0][0].transcript);
recognition.start();
```

## Troubleshooting

### "Speech recognition not supported"
- Use Chrome or Edge browser (Safari has limited support)
- Check browser permissions for microphone access

### "ODOO_PASSWORD environment variable not set"
- Set the password: `export ODOO_PASSWORD="your_password"`
- Or use command-line flag when starting server

### "Failed to authenticate with Odoo"
- Verify Odoo URL, database, username, and password
- Check network connectivity to Odoo server
- Test connection: `curl http://localhost:8000/api/test-connection`

### "CORS error" in browser
- Server already configured with CORS allow all for development
- For production, restrict `allow_origins` in `odoo_query_server.py`

### "No results found"
- Check if tickets exist in Odoo for the time period
- Try broader queries like "all tickets"
- Verify user has access to helpdesk tickets in Odoo

## Future Enhancements (Scaling Phases)

### Phase 2: Advanced NLP
- Integrate OpenAI/Claude API for better intent recognition
- Support complex multi-clause queries
- Handle typos and variations in speech

### Phase 3: Multi-Module Support
- Extend to CRM (leads, opportunities)
- Extend to Projects (tasks, milestones)
- Extend to Sales (orders, invoices)

### Phase 4: Write Operations
- "Create a ticket for euroblaze"
- "Update ticket 1234 to high priority"
- "Close ticket 1234"
- Requires confirmation dialogs for safety

### Phase 5: Multi-Language & Voice Feedback
- Support German, French, Spanish queries
- Text-to-speech responses
- Voice confirmation for actions

## Security Considerations

- **Authentication**: Currently uses single Odoo user credentials
- **Rate Limiting**: Configured at 10 queries/minute
- **Read-Only**: Only SELECT operations allowed (no INSERT/UPDATE/DELETE)
- **Input Sanitization**: Parser validates and limits query parameters
- **HTTPS**: Use HTTPS in production (configure nginx/Apache reverse proxy)

## API Rate Limits

- **Query API**: 10 requests/minute per IP
- **Odoo XML-RPC**: No specific limit (depends on Odoo configuration)
- **Result Limit**: Maximum 100 tickets per query (configurable)

##  Reminder System

**Every 5 conversations**: Review scaling phases and decide on next steps.

Current Phase: **Phase 1 - MVP Complete**

---

## Quick Reference

```bash
# Start API server
ODOO_PASSWORD=your_pass python odoo_query_server.py

# Generate report with Odoo data
./git2local --non-interactive --period=week --include-odoo

# Test query parser
python query_parser.py

# Check API health
curl http://localhost:8000/health
```

**Speech Query Patterns:**
- `"my"` + `"open"/"closed"` + `"tickets"`
- `"high"/"urgent"` + `"priority"` + `"tickets"`
- `"tickets"` + `"for"/"from"` + `"<customer>"`
- `"tickets"` + `"today"/"this week"/"this month"`
- `"show"/"list"` + `"<number>"` + `"tickets"`

**API Endpoint:** `http://localhost:8000/api/query`
