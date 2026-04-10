// TED Bot Frontend JavaScript

const API_BASE_URL = 'http://localhost:8000/api/v1';

console.log('🚀 Script loaded!');

// Check if we're on file:// protocol and warn about CORS
if (window.location.protocol === 'file:') {
    console.warn('Running from file://. CORS may block API requests. Consider serving via HTTP.');
}

// Generate or retrieve session ID
let sessionId = localStorage.getItem('ted-bot-session-id');
if (!sessionId) {
    sessionId = 'session-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);
    localStorage.setItem('ted-bot-session-id', sessionId);
    console.log('🆕 New session created:', sessionId);
} else {
    console.log('♻️ Resuming session:', sessionId);
}

// Chat messages array
let chatMessages = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== TED Bot Initializing ===');
    console.log('DOM loaded, initializing TED Bot...');
    
    // Test API connection
    fetch(`${API_BASE_URL}/health`)
        .then(res => res.json())
        .then(data => console.log('✅ Backend connected:', data))
        .catch(err => console.error('❌ Backend connection failed:', err));
    
    // Chat form
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    
    console.log('Elements found:', {
        chatForm: !!chatForm,
        chatInput: !!chatInput,
        chatMessages: !!chatMessages
    });
    
    if (chatForm) {
        chatForm.addEventListener('submit', handleChat);
        console.log('✅ Chat form handler attached');
        
        // Also add button click handler as backup
        const submitButton = chatForm.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.addEventListener('click', (e) => {
                console.log('Button clicked!');
            });
        }
    } else {
        console.error('❌ Chat form not found!');
    }
    
    // Add welcome message
    console.log('Adding welcome message...');
    const welcomeText = sessionId !== localStorage.getItem('ted-bot-session-id') || localStorage.getItem('ted-bot-first-load') !== 'done'
        ? `👋 Hello! I'm the TED Tender Search Agent.

I can help you find European public procurement opportunities using natural language.

Try asking me:
• "Find software development contracts in Germany"
• "Show me IT services tenders in France"
• "Any construction projects in Spain?"
• "Search for tenders with CPV code 72000000"

I'll search the TED database and provide detailed tender information including buyers, deadlines, and links to full notices.

💡 **Tip**: I'll remember our conversation, so you can ask follow-up questions about previous searches!`
        : `👋 Welcome back! I remember our previous conversation. Feel free to continue or ask new questions.`;
    
    addChatMessage('assistant', welcomeText);
    localStorage.setItem('ted-bot-first-load', 'done');
    
    console.log('=== Initialization complete ===');
});

// Handle chat - Chat with TED Agent
async function handleChat(e) {
    console.log('handleChat called', e);
    
    // Prevent form submission
    if (e && e.preventDefault) {
        e.preventDefault();
    }
    if (e && e.stopPropagation) {
        e.stopPropagation();
    }
    
    console.log('Form submission prevented');
    
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    console.log('Message:', message);
    
    if (!message) {
        console.log('Empty message, returning');
        return false;
    }
    
    // Add user message to UI
    addChatMessage('user', message);
    input.value = '';
    
    // Show "thinking" indicator
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message assistant thinking';
    thinkingDiv.textContent = '🤔 Searching TED database...';
    thinkingDiv.id = 'thinking-indicator';
    document.getElementById('chatMessages').appendChild(thinkingDiv);
    
    try {
        console.log('Sending request to API...', 'Session ID:', sessionId);
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId  // Send session ID for conversation continuity
            })
        });
        
        // Remove thinking indicator
        const thinking = document.getElementById('thinking-indicator');
        if (thinking) thinking.remove();
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Chat request failed');
        }
        
        const data = await response.json();
        const assistantResponse = data.response;
        
        // Add agent's response to UI
        addChatMessage('assistant', assistantResponse);
        
    } catch (error) {
        // Remove thinking indicator if still there
        const thinking = document.getElementById('thinking-indicator');
        if (thinking) thinking.remove();
        
        console.error('Chat error:', error);
        addChatMessage('assistant', `❌ Sorry, I encountered an error: ${error.message}\n\nPlease make sure the API server is running and Ollama is configured.`);
    }
    
    return false;  // Ensure form doesn't submit
}

// Add chat message to UI
function addChatMessage(role, content) {
    console.log('📝 addChatMessage called:', role, 'length:', content.length);
    
    const messagesDiv = document.getElementById('chatMessages');
    if (!messagesDiv) {
        console.error('❌ chatMessages element not found!');
        return;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    // Simple pre-wrap rendering for now
    messageDiv.style.whiteSpace = 'pre-wrap';
    messageDiv.textContent = content;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    console.log('✅ Message added successfully');
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Clear session and start fresh conversation
function clearSession() {
    if (confirm('Start a new conversation? This will clear your chat history.')) {
        localStorage.removeItem('ted-bot-session-id');
        localStorage.removeItem('ted-bot-first-load');
        location.reload();
    }
}

// Make clearSession available globally
window.clearSession = clearSession;

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
