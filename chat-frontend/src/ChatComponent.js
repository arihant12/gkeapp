import React, { useEffect, useState } from "react";
import { io } from "socket.io-client";
import axios from "axios";

const CHAT_SERVICE_URL = "http://localhost:5001";
const socket = io(CHAT_SERVICE_URL);

function ChatComponent({ sender, receiver }) {
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState("");
    const [conversations, setConversations] = useState([]);
    const [selectedChat, setSelectedChat] = useState(receiver); // ✅ Default to clicked user

    // ✅ Fetch chat history when `sender` or `selectedChat` changes
    useEffect(() => {
        if (sender && selectedChat) {
            fetchChatHistory(sender, selectedChat);
        }
    }, [selectedChat]);

    // ✅ Fetch all chats (left sidebar)
    useEffect(() => {
        if (sender) {
            fetchConversations(sender);
        }
    }, [sender]);

    // ✅ Fetch list of previous conversations
    const fetchConversations = async (userEmail) => {
        try {
            const response = await axios.get(`${CHAT_SERVICE_URL}/get_chats?user_id=${userEmail}`);
            setConversations(response.data.conversations);
        } catch (error) {
            console.error("❌ Error fetching conversations:", error);
        }
    };

    // ✅ Fetch chat history between `sender` and `receiver`
    const fetchChatHistory = async (sender, receiver) => {
        try {
            const response = await axios.get(`${CHAT_SERVICE_URL}/chat_history/${sender}/${receiver}`);
            setMessages(response.data);
        } catch (error) {
            console.error("❌ Error fetching chat history:", error);
        }
    };

    // ✅ Send a message
    const sendMessage = async () => {
        if (!messageInput.trim() || !sender || !selectedChat) return;

        const newMessage = { sender, receiver: selectedChat, message: messageInput.trim() };

        setMessages((prevMessages) => [...prevMessages, newMessage]);

        try {
            await axios.post(
                `${CHAT_SERVICE_URL}/send_message`,
                newMessage,
                { headers: { "Content-Type": "application/json" }, withCredentials: true }
            );
        } catch (error) {
            console.error("❌ Error sending message:", error);
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
        <div style={{ display: "flex" }}>
            {/* ✅ Chat List Sidebar */}
            <div style={{ width: "30%", borderRight: "1px solid #ddd", padding: "10px" }}>
                <h3>Chats</h3>
                <ul>
                    {conversations.map((conv, index) => (
                        <li 
                            key={index} 
                            onClick={() => setSelectedChat(conv.chat_partner)} // ✅ No page reload
                            style={{ cursor: "pointer", padding: "10px", borderBottom: "1px solid #eee" }}
                        >
                            {conv.chat_partner}
                        </li>
                    ))}
                </ul>
            </div>

            {/* ✅ Chat Window */}
            <div style={{ flex: 1, padding: "10px" }}>
                {sender ? (
                    selectedChat ? (
                        <>
                            <h3>Chat with {selectedChat}</h3>
                            <div style={{ border: "1px solid #ddd", padding: "10px", maxHeight: "300px", overflowY: "scroll" }}>
                                {messages.map((msg, index) => (
                                    <p key={index} style={{ 
                                        textAlign: msg.sender === sender ? "right" : "left", 
                                        backgroundColor: msg.sender === sender ? "#dcf8c6" : "#ffffff", 
                                        padding: "5px", 
                                        borderRadius: "10px" 
                                    }}>
                                        <strong>{msg.sender === sender ? "You" : msg.sender}:</strong> {msg.message}
                                    </p>
                                ))}
                            </div>
                            <input type="text" value={messageInput} onChange={(e) => setMessageInput(e.target.value)} placeholder="Type a message..." />
                            <button onClick={sendMessage}>Send</button>
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
