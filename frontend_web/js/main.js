document.addEventListener('DOMContentLoaded', () => {
    console.log("Portal de Movilidad - Sitio Web Cargado");

    // --- Authentication and Personalization Logic ---
    const loginLinkContainer = document.getElementById('login-link-container');
    const userGreetingContainer = document.getElementById('user-greeting-container');
    const userGreetingSpan = document.getElementById('user-greeting');
    const logoutButton = document.getElementById('logout-button');
    const API_BASE_URL = "http://127.0.0.1:8000";

    const checkLoginState = async () => {
        const token = localStorage.getItem('flet_client_storage.session.token');
        if (!token) {
            showLoggedOutState();
            return;
        }
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/users/me`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) {
                showLoggedOutState();
                Object.keys(localStorage).forEach(key => key.startsWith('flet_client_storage.') && localStorage.removeItem(key));
                return;
            }
            const userInfo = await response.json();
            showLoggedInState(userInfo);
        } catch (error) {
            showLoggedOutState();
        }
    };

    const showLoggedInState = (userInfo) => {
        const userName = userInfo.full_name ? userInfo.full_name.split(' ')[0] : userInfo.username;
        userGreetingSpan.textContent = `Hola, ${userName}`;
        loginLinkContainer.classList.add('hidden');
        userGreetingContainer.classList.remove('hidden');
    };

    const showLoggedOutState = () => {
        loginLinkContainer.classList.remove('hidden');
        userGreetingContainer.classList.add('hidden');
    };

    const handleLogout = () => {
        Object.keys(localStorage).forEach(key => key.startsWith('flet_client_storage.') && localStorage.removeItem(key));
        window.location.reload();
    };

    logoutButton.addEventListener('click', (e) => {
        e.preventDefault();
        handleLogout();
    });

    // --- Payment Logic ---
    const buyMonthlyPlanButton = document.getElementById('buy-monthly-plan');
    const buyYearlyPlanButton = document.getElementById('buy-yearly-plan');

    const initiatePayment = async (planId) => {
        const token = localStorage.getItem('flet_client_storage.session.token');
        if (!token) {
            alert("Por favor, inicie sesión o regístrese antes de adquirir un plan.");
            window.location.href = "/app";
            return;
        }
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/payments/create-checkout-session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ plan_id: planId })
            });
            if (!response.ok) throw new Error((await response.json()).detail || "No se pudo iniciar el proceso de pago.");
            const sessionData = await response.json();
            window.location.href = sessionData.checkout_url;
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    };

    if (buyMonthlyPlanButton) buyMonthlyPlanButton.addEventListener('click', () => initiatePayment('profesional_mensual'));
    if (buyYearlyPlanButton) buyYearlyPlanButton.addEventListener('click', () => initiatePayment('profesional_anual'));

    // --- Chat Widget Logic ---
    const chatFab = document.getElementById('chat-fab');
    const chatWidget = document.getElementById('chat-widget-container');
    const chatCloseBtn = document.getElementById('chat-close-btn');
    const chatMessages = document.getElementById('chat-widget-messages');
    const chatInput = document.getElementById('chat-widget-input');
    const chatSendBtn = document.getElementById('chat-widget-send-btn');
    const chatMicBtn = document.getElementById('chat-widget-mic-btn');

    let chatContext = {}; // To hold conversation state

    const toggleChatWidget = () => {
        chatWidget.classList.toggle('hidden');
        if (!chatWidget.classList.contains('hidden') && chatMessages.children.length === 0) {
            addMessageToChat("Hola, soy tu asistente virtual. ¿Cómo puedo ayudarte?", 'assistant');
        }
    };

    const addMessageToChat = (text, sender) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', sender);
        const textElement = document.createElement('div');
        textElement.classList.add('text');
        textElement.textContent = text;
        messageElement.appendChild(textElement);
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const handleSendMessage = async () => {
        const messageText = chatInput.value.trim();
        if (!messageText) return;

        addMessageToChat(messageText, 'user');
        chatInput.value = '';
        chatInput.disabled = true;
        chatSendBtn.disabled = true;

        try {
            const token = localStorage.getItem('flet_client_storage.session.token');
            const headers = { 'Content-Type': 'application/json' };
            if (token) headers['Authorization'] = `Bearer ${token}`;

            const response = await fetch(`${API_BASE_URL}/api/v1/chat/`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ message: messageText, context: chatContext })
            });
            if (!response.ok) throw new Error("El servicio de chat no está disponible.");

            const responseData = await response.json();
            const aiResponse = responseData.data.response_text;
            chatContext = responseData.data.new_context || {}; // Update context

            addMessageToChat(aiResponse, 'assistant');
        } catch (error) {
            addMessageToChat(`Error: ${error.message}`, 'assistant');
        } finally {
            chatInput.disabled = false;
            chatSendBtn.disabled = false;
            chatInput.focus();
        }
    };

    const handleSpeechRecognition = () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Tu navegador no soporta el reconocimiento de voz.");
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = 'es-ES';
        recognition.interimResults = false;

        recognition.onstart = () => {
            chatMicBtn.textContent = '...';
        };

        recognition.onspeechend = () => {
            recognition.stop();
            chatMicBtn.textContent = '🎙️';
        };

        recognition.onresult = (event) => {
            chatInput.value = event.results[0][0].transcript;
        };

        recognition.onerror = (event) => {
            alert(`Error de reconocimiento: ${event.error}`);
            chatMicBtn.textContent = '🎙️';
        };

        recognition.start();
    };

    chatFab.addEventListener('click', toggleChatWidget);
    chatCloseBtn.addEventListener('click', toggleChatWidget);
    chatSendBtn.addEventListener('click', handleSendMessage);
    chatInput.addEventListener('keydown', (e) => e.key === 'Enter' && handleSendMessage());
    chatMicBtn.addEventListener('click', handleSpeechRecognition);


    // --- Initial Execution ---
    checkLoginState();
});
