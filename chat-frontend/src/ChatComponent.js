import React, { useEffect, useState, useRef } from "react";
import { io } from "socket.io-client";
import axios from "axios";
import "./ChatComponent.css"; // ✅ Import the new CSS file

const CHAT_SERVICE_URL = "http://localhost:5001";
const socket = io(CHAT_SERVICE_URL);

function ChatComponent({ sender, receiver }) {
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState("");
    const [conversations, setConversations] = useState([]);
    const [selectedChat, setSelectedChat] = useState(receiver);
    const messagesEndRef = useRef(null); // ✅ Auto-scroll reference

    // ✅ Fetch chat history when sender or selectedChat changes
    useEffect(() => {
        if (sender && selectedChat) {
            fetchChatHistory(sender, selectedChat);
        }
    }, [selectedChat]);

    // ✅ Fetch previous conversations (left sidebar)
    useEffect(() => {
        if (sender) {
            fetchConversations(sender);
        }
    }, [sender]);

    // ✅ Auto-scroll to the latest message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // ✅ Fetch chat history
    const fetchChatHistory = async (sender, receiver) => {
        try {
            const response = await axios.get(`${CHAT_SERVICE_URL}/chat_history/${sender}/${receiver}`);
            setMessages(response.data);
        } catch (error) {
            console.error("❌ Error fetching chat history:", error);
        }
    };

    // ✅ Fetch all conversations
    const fetchConversations = async (userEmail) => {
        try {
            const response = await axios.get(`${CHAT_SERVICE_URL}/get_chats?user_id=${userEmail}`);
            setConversations(response.data.conversations);
        } catch (error) {
            console.error("❌ Error fetching conversations:", error);
        }
    };

    // ✅ Send a message
    const sendMessage = async () => {
        if (!messageInput.trim() || !sender || !selectedChat) return;

        const newMessage = { sender, receiver: selectedChat, message: messageInput.trim() };

        // ✅ Try WebSocket first
        try {
            socket.emit("send_message", newMessage); // 🔥 Send via WebSocket
            setMessages((prevMessages) => [...prevMessages, newMessage]);
        } catch (error) {
            console.error("⚠️ WebSocket failed, trying HTTP...", error);

            // ✅ Fallback to HTTP API
            try {
                await axios.post(`${CHAT_SERVICE_URL}/send_message`, newMessage, {
                    headers: { "Content-Type": "application/json" },
                    withCredentials: true, // Ensure cookies/session
                });
            } catch (httpError) {
                console.error("❌ HTTP Fallback Failed:", httpError);
            }
        }

        setMessageInput("");
    };

    // ✅ Listen for new messages
    useEffect(() => {
        socket.on("receive_message", (data) => {
            setMessages((prevMessages) => [...prevMessages, data]);
        });

        return () => {
            socket.off("receive_message");
        };
    }, []);

    return (
        <div className="chat-container">
            {/* ✅ Left Sidebar - Chat List */}
            <div className="chat-sidebar">
                <h3>Chats</h3>
                <ul>
                    {conversations.map((conv, index) => (
                        <li 
                            key={index} 
                            onClick={() => setSelectedChat(conv.chat_partner)}
                            className={selectedChat === conv.chat_partner ? "active-chat" : ""}
                        >
                            {conv.chat_partner}
                        </li>
                    ))}
                </ul>
            </div>

            {/* Chat Window */}
            <div className="chat-window">
                {sender ? (
                    selectedChat ? (
                        <>
                            <h3>Chat with {selectedChat}</h3>
                            
                            <div className="message-container">
                                {messages.map((msg, index) => (
                                    <div 
                                        key={index} 
                                        className={`message ${msg.sender === sender ? "sent" : "received"}`}
                                    >
                                        <strong>{msg.sender === sender ? "You" : msg.sender}:</strong> {msg.message}
                                    </div>
                                ))}
                                <div ref={messagesEndRef}></div> {/* Auto-scroll target */}
                            </div>

                            {/* Reply Box */}
                            <div className="message-input">
                                <input 
                                    type="text" 
                                    value={messageInput} 
                                    onChange={(e) => setMessageInput(e.target.value)} 
                                    placeholder="Type a message..." 
                                />
                                <button onClick={sendMessage}>Send</button>
                            </div>
                        </>
                    ) : (
                        <h3>Select a chat to start messaging</h3>
                    )
                ) : (
                    <>
                        <h3>Authentication required</h3>
                        <p>Please log in from the main dashboard.</p>
                    </>
                )}
            </div>

        </div>
    );
}

export default ChatComponent;
