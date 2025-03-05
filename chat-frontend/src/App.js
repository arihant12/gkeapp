import React from "react";
import ChatComponent from "./ChatComponent";

function App() {
    // ✅ Extract sender (logged-in user) and receiver (clicked user) from URL
    const urlParams = new URLSearchParams(window.location.search);
    const sender = urlParams.get("loggedInuser") || null; // ✅ Logged-in user (Sender)
    const receiver = urlParams.get("receiver") || null; // ✅ Clicked user (Receiver)

    return (
        <div>
            {sender ? (
                <>
                    <ChatComponent sender={sender} receiver={receiver} />
                </>
            ) : (
                <>
                    <h3>Authentication required</h3>
                    <p>Please log in from the main dashboard.</p>
                </>
            )}
        </div>
    );
}

export default App;
