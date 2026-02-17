document.addEventListener('DOMContentLoaded', () => {
    // Inject Chat UI
    const chatContainer = document.createElement('div');
    chatContainer.id = 'engia-chat-widget';
    chatContainer.innerHTML = `
        <div class="chat-toggle-btn" id="chat-toggle">
            💬
        </div>
        <div class="chat-window" id="chat-window">
            <div class="chat-header">
                <h3>EngIA Assistant</h3>
                <span class="close-chat" id="close-chat">×</span>
            </div>
            <div class="chat-messages" id="chat-messages">
                <div class="message bot-message">
                    Hello! I'm here to help you configure your network devices. Ask me anything!
                </div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="chat-input" placeholder="Type your question..." />
                <button id="send-chat-btn">➤</button>
            </div>
        </div>
    `;
    document.body.appendChild(chatContainer);

    // Styles
    const style = document.createElement('style');
    style.textContent = `
        #engia-chat-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .chat-toggle-btn {
            width: 60px;
            height: 60px;
            background: #2c3e50;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }
        .chat-toggle-btn:hover {
            transform: scale(1.1);
        }
        .chat-window {
            display: none;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            flex-direction: column;
            overflow: hidden;
            position: absolute;
            bottom: 80px;
            right: 0;
            border: 1px solid #ddd;
        }
        .chat-header {
            background: #2c3e50;
            color: white;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-header h3 { margin: 0; font-size: 1.1rem; }
        .close-chat { cursor: pointer; font-size: 1.5rem; }
        .chat-messages {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 8px;
            max-width: 80%;
            font-size: 0.95rem;
            line-height: 1.4;
        }
        .bot-message {
            background: #e9ecef;
            color: #333;
            align-self: flex-start;
            margin-right: auto;
        }
        .user-message {
            background: #3498db;
            color: white;
            align-self: flex-end;
            margin-left: auto;
        }
        .chat-input-area {
            padding: 10px;
            border-top: 1px solid #eee;
            display: flex;
            background: white;
        }
        #chat-input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 20px;
            outline: none;
        }
        #send-chat-btn {
            background: none;
            border: none;
            font-size: 1.2rem;
            color: #3498db;
            cursor: pointer;
            margin-left: 10px;
        }
    `;
    document.head.appendChild(style);

    // Event Listeners
    const toggleBtn = document.getElementById('chat-toggle');
    const chatWindow = document.getElementById('chat-window');
    const closeChat = document.getElementById('close-chat');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-chat-btn');
    const messagesContainer = document.getElementById('chat-messages');

    let isOpen = false;

    function toggleChat() {
        isOpen = !isOpen;
        chatWindow.style.display = isOpen ? 'flex' : 'none';
        if (isOpen) chatInput.focus();
    }

    toggleBtn.addEventListener('click', toggleChat);
    closeChat.addEventListener('click', toggleChat);

    function addMessage(text, isUser) {
        const div = document.createElement('div');
        div.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        // Basic Markdown Support for formatting (Bold)
        div.innerHTML = text.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
        
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        addMessage(text, true);
        chatInput.value = '';

        // Gather Context
        const vendorSelect = document.getElementById('vendor');
        const context = {
            vendor: vendorSelect ? vendorSelect.value : null,
            // Add more context fields as needed
        };

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': '' // Only if needed in future
                },
                body: JSON.stringify({ message: text, context: context })
            });

            const data = await response.json();
            addMessage(data.response, false);

        } catch (error) {
            console.error('Chat Error:', error);
            addMessage("Sorry, I'm having trouble connecting to the server.", false);
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});
