document.addEventListener('DOMContentLoaded', () => {
    console.log("Portal de Movilidad - Sitio Web Cargado");

    const loginLinkContainer = document.getElementById('login-link-container');
    const userGreetingContainer = document.getElementById('user-greeting-container');
    const userGreetingSpan = document.getElementById('user-greeting');
    const logoutButton = document.getElementById('logout-button');

    const API_BASE_URL = "http://127.0.0.1:8000"; // Should match your backend URL

    /**
     * Checks for an auth token in localStorage and updates the UI accordingly.
     */
    const checkLoginState = async () => {
        // Flet prepends 'flet_client_storage.' to the keys.
        const token = localStorage.getItem('flet_client_storage.session.token');

        if (!token) {
            console.log("No auth token found. User is logged out.");
            showLoggedOutState();
            return;
        }

        console.log("Auth token found. Verifying with server...");
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/users/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                // If token is invalid (e.g., expired), server will return 401
                console.error("Token verification failed:", response.statusText);
                showLoggedOutState();
                // Clean up invalid token
                localStorage.removeItem('flet_client_storage.session.token');
                localStorage.removeItem('flet_client_storage.session.user_info');
                return;
            }

            const userInfo = await response.json();
            console.log("User info received:", userInfo);
            showLoggedInState(userInfo);

        } catch (error) {
            console.error("Error fetching user data:", error);
            showLoggedOutState();
        }
    };

    /**
     * Updates the UI to show the logged-in state.
     * @param {object} userInfo - The user information object from the API.
     */
    const showLoggedInState = (userInfo) => {
        const userName = userInfo.full_name ? userInfo.full_name.split(' ')[0] : userInfo.username;
        userGreetingSpan.textContent = `Hola, ${userName}`;

        loginLinkContainer.classList.add('hidden');
        userGreetingContainer.classList.remove('hidden');
    };

    /**
     * Updates the UI to show the logged-out state.
     */
    const showLoggedOutState = () => {
        loginLinkContainer.classList.remove('hidden');
        userGreetingContainer.classList.add('hidden');
    };

    /**
     * Handles the logout process.
     */
    const handleLogout = () => {
        console.log("Logging out...");
        // Flet's client_storage.clear_async() removes all keys with the prefix.
        // We need to find all keys that start with 'flet_client_storage.' and remove them.
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith('flet_client_storage.')) {
                localStorage.removeItem(key);
            }
        });
        showLoggedOutState();
        // Optionally, redirect or just refresh to reflect the state change.
        window.location.reload();
    };

    // --- Event Listeners ---
    logoutButton.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent the link from navigating
        handleLogout();
    });

    // --- Initial Execution ---
    checkLoginState();


    // --- Payment Logic ---
    const buyMonthlyPlanButton = document.getElementById('buy-monthly-plan');
    const buyYearlyPlanButton = document.getElementById('buy-yearly-plan');

    const initiatePayment = async (planId) => {
        const token = localStorage.getItem('flet_client_storage.session.token');
        if (!token) {
            alert("Por favor, inicie sesión o regístrese antes de adquirir un plan.");
            // Redirect to login/register page if it exists, or the app main page
            window.location.href = "/app";
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/payments/create-checkout-session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ plan_id: planId })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "No se pudo iniciar el proceso de pago.");
            }

            const sessionData = await response.json();
            // Redirect to the simulated payment success page
            window.location.href = sessionData.checkout_url;

        } catch (error) {
            console.error("Error initiating payment:", error);
            alert(`Error: ${error.message}`);
        }
    };

    if (buyMonthlyPlanButton) {
        buyMonthlyPlanButton.addEventListener('click', () => initiatePayment('profesional_mensual'));
    }
    if (buyYearlyPlanButton) {
        buyYearlyPlanButton.addEventListener('click', () => initiatePayment('profesional_anual'));
    }
    // Note: The trial button is not handled as it doesn't require payment.
});
