/* rasa-voice-chat-widget.js - FINAL STABLE VERSION (FIXED INITIAL INTENT TIMING) */

// --- Configuration Constants ---
const RASA_REST_URL = "http://77.125.130.211:5005/webhooks/rest/webhook";
const RASA_BOT_NAME = "Support Agent";
const BOT_ICON_URL = "https://img.icons8.com/fluent/48/000000/robot.png";
const INITIAL_INTENT = "/get_started"; 

// --- Session Management ---
let conversationId = sessionStorage.getItem('conversationId');
if (!conversationId) {
    conversationId = 'rasa-user-' + Math.random().toString(36).substring(2, 9);
    sessionStorage.setItem('conversationId', conversationId);
    console.log(`[Rasa Widget] New Session ID created: ${conversationId}`);
} else {
    console.log(`[Rasa Widget] Existing Session ID loaded: ${conversationId}`);
}

// --- Global State and Voice Configuration ---
const synth = window.speechSynthesis;
let selectedVoice = null;
let voices = [];
let isMessageBeingSent = false; 
let initialMessageSent = false; 

function loadVoices() {
    voices = synth.getVoices();
    const voiceSelector = document.getElementById('voice-selector');
    if (!voiceSelector) return;

    voiceSelector.innerHTML = '<option value="">Select Voice</option>';
    voices.forEach((voice) => {
        const option = document.createElement('option');
        option.value = voice.name;
        option.textContent = `${voice.name} (${voice.lang.substring(0, 2)})`;
        voiceSelector.appendChild(option);
    });

    const lastSelected = sessionStorage.getItem('selectedVoiceName');
    if (lastSelected) {
        voiceSelector.value = lastSelected;
        selectedVoice = voices.find(v => v.name === lastSelected);
    } else {
        selectedVoice = voices.find(v => v.lang.startsWith('en')) || voices[0];
        if (selectedVoice) voiceSelector.value = selectedVoice.name;
    }

    voiceSelector.addEventListener('change', (e) => {
        const voiceName = e.target.value;
        selectedVoice = voices.find(v => v.name === voiceName);
        sessionStorage.setItem('selectedVoiceName', voiceName);
    });
}

if (synth) {
    if (synth.onvoiceschanged !== undefined) {
        synth.onvoiceschanged = loadVoices;
    }
    loadVoices();
}

// --- HTML Structure Injection ---
document.addEventListener('DOMContentLoaded', () => {
    const widgetHTML = `
        <div id="rasa-chat-widget">
            <button id="chat-toggle-btn" class="chat-closed">Chat</button>
            <div id="chat-panel" class="hidden">
                <div id="chat-header">
                    <img src="${BOT_ICON_URL}" alt="Assistant Icon" id="assistant-icon">
                    <span id="assistant-name">${RASA_BOT_NAME}</span>
                    <select id="voice-selector"></select>
                </div>
                <div id="chat-box">
                    <div class="message bot-message initial-message">
                        <img src="${BOT_ICON_URL}" class="bot-icon" alt="Bot Icon">
                        <div class="message-bubble">
                            <div class="message-text">
                                Connecting to Rasa... ID: ${conversationId.slice(-6)}
                            </div>
                        </div>
                    </div>
                </div>
                <div id="chat-controls">
                    <input type="text" id="user-input" placeholder="Type a message or use the microphone...">
                    <button id="send-btn">Send</button>
                    <button id="mic-btn" title="Start Voice Input">
                        <span class="mic-icon">MIC</span> 
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', widgetHTML);

    document.getElementById('chat-toggle-btn').addEventListener('click', toggleChatPanel);
    document.getElementById('send-btn').addEventListener('click', () => handleUserInput());
    document.getElementById('user-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleUserInput();
    });

    setupVoiceInput();
    loadVoices();
    
    // FIX: Delay the initial message slightly to ensure all setup is complete, 
    // especially for asynchronous tasks like voice loading.
    setTimeout(sendInitialMessage, 500); 
});

// --- Core Functionality ---

function sendInitialMessage() {
    if (!initialMessageSent) {
        console.log(`[Rasa Widget] Attempting to send initial intent: ${INITIAL_INTENT}`);
        // Send the initial intent as the message and payload
        sendToRasa(INITIAL_INTENT, INITIAL_INTENT);
        initialMessageSent = true;
    }
}

function toggleChatPanel() {
    const panel = document.getElementById('chat-panel');
    const button = document.getElementById('chat-toggle-btn');
    panel.classList.toggle('hidden');
    button.classList.toggle('chat-closed');
    button.classList.toggle('chat-open');
    button.textContent = panel.classList.contains('hidden') ? 'Chat' : 'Close';
    if (!panel.classList.contains('hidden')) {
        document.getElementById('user-input').focus();
    }
}

function appendMessage(sender, text, imageUrl) {
    const chatBox = document.getElementById('chat-box');
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender + '-message');

    let bubbleContent = '';
    
    if (text) {
        bubbleContent += `<div class="message-text">${text}</div>`;
    }
    if (imageUrl) {
        bubbleContent += `<img src="${imageUrl}" class="bot-image" alt="Bot image">`;
    }
    
    if (sender === 'bot') {
        msgDiv.innerHTML = `<img src="${BOT_ICON_URL}" class="bot-icon" alt="Bot Icon"><div class="message-bubble">${bubbleContent}</div>`;
    } else { 
        msgDiv.innerHTML = `<div class="message-bubble">${bubbleContent}</div>`;
    }
    
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function speakBotMessage(text) {
    if (!synth || !selectedVoice) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = selectedVoice;
    synth.speak(utterance);
}

async function sendToRasa(message, payload = null) {
    const chatBox = document.getElementById('chat-box');
    const msgToSend = payload !== null ? payload : message;

    const requestBody = { 
        sender: conversationId, 
        message: String(msgToSend) 
    };

    console.log('[Rasa Widget] Sending Request Body:', requestBody);

    // Only add a typing indicator if a button click or user input (not the initial intent) is being sent
    let thinkingMessage = null;
    if (!isMessageBeingSent) {
        thinkingMessage = document.createElement('div');
        thinkingMessage.classList.add('message', 'bot-message', 'thinking');
        thinkingMessage.innerHTML = `<img src="${BOT_ICON_URL}" class="bot-icon" alt="Bot Icon"><div class="message-bubble"><div class="message-text">...typing</div></div>`;
        chatBox.appendChild(thinkingMessage);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    isMessageBeingSent = true;

    try {
        const res = await fetch(RASA_REST_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody)
        });

        if (!res.ok) {
            const errorText = await res.text();
            throw new Error(`HTTP Error: ${res.status} ${res.statusText}. Response: ${errorText}`);
        }

        const messages = await res.json();
        if(thinkingMessage && chatBox.contains(thinkingMessage)) chatBox.removeChild(thinkingMessage);

        if (messages.length === 0 && msgToSend !== INITIAL_INTENT) {
             console.warn("[Rasa Widget] Received empty response array from Rasa.");
             appendMessage('bot', 'Received no response. Check Rasa logs for NLU/Dialogue issues.', null);
        }

        messages.forEach(msg => {
            if (msg.text || msg.image) {
                appendMessage('bot', msg.text, msg.image);
                if (msg.text) speakBotMessage(msg.text);
            }
            if (msg.buttons && msg.buttons.length > 0) {
                displayButtons(msg.buttons);
            }
        });

    } catch (error) {
        console.error("[Rasa Widget] Fatal Communication Error:", error);
        if(thinkingMessage && chatBox.contains(thinkingMessage)) chatBox.removeChild(thinkingMessage);
        appendMessage('bot', `❌ Error: ${error.message}. Is the server running at ${RASA_REST_URL}?`, null);
    } finally {
        isMessageBeingSent = false;
    }
}

async function handleUserInput(isVoice = false, voiceText = '') {
    const inputEl = document.getElementById('user-input');
    const message = isVoice ? voiceText : inputEl.value.trim();

    if (message === '' || isMessageBeingSent) return;

    appendMessage('user', message);
    inputEl.value = ''; 
    await sendToRasa(message);
}

function displayButtons(buttons) {
    const chatBox = document.getElementById('chat-box');
    const buttonContainer = document.createElement('div');
    buttonContainer.classList.add('button-container');

    buttons.forEach(button => {
        const btn = document.createElement('button');
        btn.classList.add('rasa-button');
        btn.textContent = button.title;

        btn.onclick = () => {
            if (isMessageBeingSent) return;

            const msgToSend = button.payload || button.title; 
            
            appendMessage('user', button.title);
            sendToRasa(msgToSend, msgToSend);
            buttonContainer.remove();
        };

        buttonContainer.appendChild(btn);
    });

    chatBox.appendChild(buttonContainer);
    chatBox.scrollTop = chatBox.scrollHeight;
}


// --- Speech-to-Text Setup ---
function setupVoiceInput() {
    const micBtn = document.getElementById('mic-btn');
    const micIcon = micBtn ? micBtn.querySelector('.mic-icon') : null;
    
    if (!micBtn || !micIcon) {
        console.warn("[Rasa Widget] Microphone button or icon not found in DOM.");
        return;
    }
    
    if (!('webkitSpeechRecognition' in window)) {
        console.warn("[Rasa Widget] webkitSpeechRecognition not supported. Hiding microphone button.");
        micBtn.style.display = 'none';
        return;
    }

    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    let isRecording = false;

    micBtn.addEventListener('click', () => {
        if (isRecording) {
            recognition.stop();
        } else {
            document.getElementById('user-input').value = 'Listening...'; 
            recognition.start();
        }
    });

    recognition.onstart = () => {
        isRecording = true;
        micIcon.textContent = 'REC';
        micBtn.title = 'Stop Recording';
        micBtn.classList.add('recording');
        document.getElementById('user-input').value = 'Speak now...';
    };

    recognition.onresult = (event) => {
        const finalTranscript = Array.from(event.results)
            .filter(result => result.isFinal)
            .map(result => result[0].transcript)
            .join('');

        if (finalTranscript.length > 0) {
            document.getElementById('user-input').value = finalTranscript;
            handleUserInput(true, finalTranscript);
        }
    };
    
    recognition.onend = () => {
        isRecording = false;
        micIcon.textContent = 'MIC';
        micBtn.title = 'Start Voice Input';
        micBtn.classList.remove('recording');
        if (document.getElementById('user-input').value === 'Speak now...') {
             document.getElementById('user-input').value = ''; 
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (isRecording) {
            micIcon.textContent = 'MIC';
            micBtn.classList.remove('recording');
            document.getElementById('user-input').value = 'Error listening. Try again.';
            isRecording = false;
        }
    };
}

	
