import React, { useEffect, useState } from "react";
import { io } from "socket.io-client";
import axios from "axios";
import { auth, provider, signInWithPopup } from "./firebaseConfig";
import { onAuthStateChanged, signOut } from "firebase/auth";

// ✅ Connect to Chat Microservice directly
const CHAT_SERVICE_URL = "http://localhost:5001"; // Change for Kubernetes deployment
const socket = io(CHAT_SERVICE_URL);

function ChatComponent() {
  const [messages, setMessages] = useState([]); // Stores chat messages
  const [messageInput, setMessageInput] = useState(""); // Stores input message text
  const [currentUser, setCurrentUser] = useState(null); // Stores logged-in user
  const [receiverEmail, setReceiverEmail] = useState(""); // Stores receiver's email

  // ✅ Get receiver email from URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    setReceiverEmail(urlParams.get("receiver") || "");
  }, []);

  // ✅ Check Firebase Auth State
  useEffect(() => {
    onAuthStateChanged(auth, (user) => {
      if (user) {
        setCurrentUser(user.email);
        fetchChatHistory(user.email, receiverEmail);
      } else {
        setCurrentUser(null);
      }
    });
  }, [receiverEmail]);

  // ✅ Google Sign-In
  const handleGoogleSignIn = async () => {
    try {
      const result = await signInWithPopup(auth, provider);
      setCurrentUser(result.user.email);
    } catch (error) {
      console.error("❌ Error signing in:", error);
    }
  };

  // ✅ Logout
  const handleLogout = async () => {
    try {
      await signOut(auth);
      setCurrentUser(null);
    } catch (error) {
      console.error("❌ Error logging out:", error);
    }
  };

  // ✅ Fetch chat history from Chat Service
  const fetchChatHistory = async (sender, receiver) => {
    if (!sender || !receiver) return;
    try {
      const response = await axios.get(`${CHAT_SERVICE_URL}/chat_history/${sender}/${receiver}`);
      setMessages(response.data);
    } catch (error) {
      console.error("❌ Error fetching chat history:", error);
    }
  };

  // ✅ Send a message directly to Chat Service & Update UI Instantly
  const sendMessage = () => {
    if (!messageInput.trim() || !currentUser) return;

    const newMessage = {
      sender: currentUser,
      receiver: receiverEmail,
      message: messageInput.trim(),
    };

    // ✅ Optimistically update UI (message appears instantly)
    setMessages((prevMessages) => [...prevMessages, newMessage]);

    // ✅ Send message to WebSocket server
    socket.emit("send_message", newMessage);

    // ✅ Clear input field
    setMessageInput("");
  };

  // ✅ Listen for new messages from WebSocket
  useEffect(() => {
    socket.on("receive_message", (data) => {
      setMessages((prevMessages) => [...prevMessages, data]); // Append new messages
    });

    return () => {
      socket.off("receive_message"); // Cleanup listener when component unmounts
    };
  }, []);

  return (
    <div>
      {currentUser ? (
        <>
          <h3>Chat with {receiverEmail}</h3>
          <button onClick={handleLogout}>Logout</button>
          <div style={{ border: "1px solid #ddd", padding: "10px", maxHeight: "300px", overflowY: "scroll" }}>
            {messages.map((msg, index) => (
              <p key={index} style={{ 
                textAlign: msg.sender === currentUser ? "right" : "left", 
                backgroundColor: msg.sender === currentUser ? "#dcf8c6" : "#ffffff", 
                padding: "5px", 
                borderRadius: "10px" 
              }}>
                <strong>{msg.sender === currentUser ? "You" : msg.sender}:</strong> {msg.message}
              </p>
            ))}
          </div>
          <input
            type="text"
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            placeholder="Type a message..."
          />
          <button onClick={sendMessage}>Send</button>
        </>
      ) : (
        <>
          <h3>Sign in to start chatting</h3>
          <button onClick={handleGoogleSignIn}>Sign in with Google</button>
        </>
      )}
    </div>
  );
}

export default ChatComponent;
