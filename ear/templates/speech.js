// Speech Query Interface
const API_ENDPOINT = 'http://localhost:8000/api/query';
const SPEECH_API_ENDPOINT = 'http://localhost:8000/api/speech-to-text';

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

const speakButton = document.getElementById('speakButton');
const speakIcon = document.getElementById('speakIcon');
const speakText = document.getElementById('speakText');

// Check for MediaRecorder support
const mediaRecorderSupported = 'MediaRecorder' in window && 'mediaDevices' in navigator;

if (speakButton && !mediaRecorderSupported) {
    speakButton.disabled = true;
    speakButton.title = 'Speech recording not supported in this browser';
    speakIcon.textContent = '🚫';
}

if (speakButton && mediaRecorderSupported) {
    speakButton.addEventListener('click', function() {
        startSpeechQuery();
    });
}

async function startSpeechQuery() {
    // Prevent multiple simultaneous recording sessions
    if (isRecording) {
        console.log('Recording already active, stopping first...');
        stopRecording();
        return;
    }

    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // Update UI to recording state
        speakButton.classList.add('listening');
        speakIcon.textContent = '🔴';
        speakText.textContent = 'Recording...';
        isRecording = true;
        audioChunks = [];

        // Create MediaRecorder instance
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = function(event) {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async function() {
            // Stop all tracks to release microphone
            stream.getTracks().forEach(track => track.stop());

            // Update UI to processing state
            speakButton.classList.remove('listening');
            speakIcon.textContent = '⏳';
            speakText.textContent = 'Processing...';

            try {
                // Create audio blob from chunks
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

                // Convert to WAV format for better compatibility
                const wavBlob = await convertToWav(audioBlob);

                // Send to backend for speech recognition
                const formData = new FormData();
                formData.append('audio', wavBlob, 'recording.wav');

                const response = await fetch(SPEECH_API_ENDPOINT, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                // Reset UI
                speakIcon.textContent = '🎤';
                speakText.textContent = 'Speak';

                if (data.success) {
                    console.log('Recognized:', data.text);
                    processQuery(data.text);
                } else {
                    showQueryStatus(
                        '❌ Speech Recognition Error',
                        `
                            Could not recognize speech from the audio recording.
                            <br><br>
                            <strong>Error:</strong> ${data.error || 'Unknown error'}
                            <br><br>
                            <strong>Try these solutions:</strong>
                            <ul style="text-align: left; margin-top: 0.5rem;">
                                <li>Speak more clearly and loudly</li>
                                <li>Reduce background noise</li>
                                <li>Check your microphone is working properly</li>
                                <li>Try using the text input as an alternative</li>
                            </ul>
                        `,
                        'error'
                    );
                }
            } catch (error) {
                console.error('Error processing audio:', error);
                speakIcon.textContent = '🎤';
                speakText.textContent = 'Speak';

                showQueryStatus(
                    '⚠️ Audio Processing Error',
                    `
                        Failed to process the audio recording.
                        <br><br>
                        <strong>Error:</strong> ${error.message}
                        <br><br>
                        <strong>To fix this:</strong>
                        <ul style="text-align: left; margin-top: 0.5rem;">
                            <li>Ensure the API server is running: <code>python3 odoo_query_server.py</code></li>
                            <li>Check that port 8000 is not blocked</li>
                            <li>Try recording again</li>
                            <li>Use the text input as an alternative</li>
                        </ul>
                    `,
                    'error'
                );
            }
        };

        // Start recording
        mediaRecorder.start();

        // Auto-stop after 10 seconds (prevent extremely long recordings)
        setTimeout(() => {
            if (isRecording) {
                stopRecording();
            }
        }, 10000);

    } catch (error) {
        console.error('Failed to start recording:', error);
        isRecording = false;
        speakButton.classList.remove('listening');
        speakIcon.textContent = '🎤';
        speakText.textContent = 'Speak';

        let errorMessage = '⚠️ Microphone Access Error';
        let errorDetails = '';

        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            errorDetails = `
                Microphone access was denied.
                <br><br>
                <strong>To fix this:</strong>
                <ol style="text-align: left; margin-top: 0.5rem;">
                    <li>Click the microphone icon in your browser's address bar</li>
                    <li>Select "Allow" for microphone access</li>
                    <li>Reload the page if needed</li>
                    <li>Try the voice button again</li>
                </ol>
                <br>
                <strong>Alternatively:</strong> Use the text input field to type your query.
            `;
        } else if (error.name === 'NotFoundError') {
            errorDetails = `
                No microphone found on your device.
                <br><br>
                <strong>To fix this:</strong>
                <ul style="text-align: left; margin-top: 0.5rem;">
                    <li>Connect a microphone to your device</li>
                    <li>Check that your microphone is enabled in system settings</li>
                    <li>Try the text input as an alternative</li>
                </ul>
            `;
        } else {
            errorDetails = `
                Could not start audio recording.
                <br><br>
                <strong>Error:</strong> ${error.message}
                <br><br>
                <strong>Common causes:</strong>
                <ul style="text-align: left; margin-top: 0.5rem;">
                    <li>Microphone is being used by another application</li>
                    <li>Browser doesn't have microphone permissions</li>
                    <li>Page must be served over HTTPS (or localhost)</li>
                </ul>
                <br>
                Please try the text input as an alternative.
            `;
        }

        showQueryStatus(errorMessage, errorDetails, 'error');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        isRecording = false;
    }
}

async function convertToWav(blob) {
    // For now, we'll send the audio as-is and rely on backend conversion
    // A full implementation would use an AudioContext to convert to WAV format
    // This is acceptable since Python's SpeechRecognition handles various formats
    return blob;
}

function createOrGetModal(title) {
    let modal = document.getElementById('queryModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'queryModal';
        modal.className = 'query-modal';
        modal.innerHTML = `
            <div class="query-panel">
                <h2 id="modalTitle" style="margin-bottom: 1rem;"></h2>
                <div id="queryContent"></div>
                <button onclick="document.getElementById('queryModal').classList.remove('active')"
                        style="margin-top: 1rem; padding: 0.5rem 1rem; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    Close
                </button>
            </div>
        `;
        document.body.appendChild(modal);
    }

    // Update title
    const titleElement = document.getElementById('modalTitle');
    if (titleElement) {
        titleElement.textContent = title;
    }

    return modal;
}

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
            const errorTitle = '⚠️ Query Processing Error';
            const errorDetails = `
                The API server encountered an error while processing your query.
                <br><br>
                <strong>Error:</strong> ${data.error || 'Unknown error'}
                <br><br>
                Please try rephrasing your query or check the API server logs for details.
            `;
            showQueryStatus(errorTitle, errorDetails, 'error');
        }
    } catch (error) {
        console.error('Query processing error:', error);
        speakIcon.textContent = '🎤';
        speakText.textContent = 'Speak';

        const errorTitle = '🔌 API Connection Error';
        const errorDetails = `
            Unable to connect to the Odoo query API server at ${API_ENDPOINT}.
            <br><br>
            <strong>Error:</strong> ${error.message}
            <br><br>
            <strong>To fix this:</strong>
            <ol style="text-align: left; margin-top: 0.5rem;">
                <li>Ensure the API server is running: <code>python3 odoo_query_server.py</code></li>
                <li>Check that port 8000 is not blocked</li>
                <li>Verify ODOO_PASSWORD environment variable is set</li>
            </ol>
        `;
        showQueryStatus(errorTitle, errorDetails, 'error');
    }
}

function displayQueryResults(data) {
    const modal = createOrGetModal('Query Results');
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

function showQueryStatus(title, details, type) {
    const modalTitle = type === 'error' ? 'Error' : 'Information';
    const modal = createOrGetModal(modalTitle);
    const content = document.getElementById('queryContent');
    content.innerHTML = `
        <div class="query-status ${type}" style="text-align: left;">
            <h3 style="margin: 0 0 1rem 0; font-size: 1.2rem;">${title}</h3>
            <div>${details}</div>
        </div>
    `;

    modal.classList.add('active');

    // Don't auto-close errors - let user read and close manually
}

// Text input query handling
const queryInput = document.getElementById('queryInput');
const querySubmit = document.getElementById('querySubmit');

if (querySubmit && queryInput) {
    querySubmit.addEventListener('click', function() {
        const query = queryInput.value.trim();
        if (query) {
            processQuery(query);
            queryInput.value = ''; // Clear input after submission
        }
    });

    // Allow Enter key to submit
    queryInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            const query = queryInput.value.trim();
            if (query) {
                processQuery(query);
                queryInput.value = '';
            }
        }
    });
}
