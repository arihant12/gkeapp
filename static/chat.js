// ✅ Make sure everything loads before executing
window.onload = function () {
    console.log("✅ chat.js Loaded");

    const socket = io("http://localhost:5001");

    function getQueryParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    }

    const receiverEmail = getQueryParam("receiver");
    document.getElementById("chat-with").innerText = receiverEmail || "Unknown User";

    let currentUserEmail = "";

    firebase.auth().onAuthStateChanged(user => {
        if (user) {
            currentUserEmail = user.email;
            console.log("✅ Logged in as:", currentUserEmail);

            socket.emit("join_chat", { sender: currentUserEmail, receiver: receiverEmail });

            loadChatHistory();
        } else {
            alert("⚠️ Please log in first!");
            window.location.href = "/login.html";
        }
    });

    function loadChatHistory() {
        fetch(`/chat_history/${currentUserEmail}/${receiverEmail}`)
            .then(response => response.json())
            .then(messages => {
                const messageContainer = document.getElementById("message-container");
                messageContainer.innerHTML = "";

                messages.forEach(msg => {
                    const messageElement = document.createElement("div");
                    messageElement.classList.add("message");
                    messageElement.classList.add(msg.sender === currentUserEmail ? "sent" : "received");
                    messageElement.innerText = `${msg.sender}: ${msg.message}`;
                    messageContainer.appendChild(messageElement);
                });
            })
            .catch(error => console.error("❌ Error loading chat history:", error));
    }

    // ✅ Attach sendMessage to window explicitly
    window.sendMessage = function () {
        console.log("📤 Sending message...");
        const messageInput = document.getElementById("message-input");
        const message = messageInput.value.trim();

        if (!message) return;

        const data = { sender: currentUserEmail, receiver: receiverEmail, message };
        socket.emit("send_message", data);
        messageInput.value = "";
    };

    // ✅ Listen for incoming messages
    socket.on("receive_message", data => {
        console.log("📩 Message received:", data);
        const messageContainer = document.getElementById("message-container");
        const messageElement = document.createElement("div");

        messageElement.classList.add("message");
        messageElement.classList.add(data.sender === currentUserEmail ? "sent" : "received");
        messageElement.innerText = `${data.sender}: ${data.message}`;
        messageContainer.appendChild(messageElement);
    });
};
