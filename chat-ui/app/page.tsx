"use client";

import {
  ChatBubble,
  ChatBubbleAvatar,
  ChatBubbleMessage,
} from "@/components/ui/chat/chat-bubble";
import { ChatInput } from "@/components/ui/chat/chat-input";
import { ChatMessageList } from "@/components/ui/chat/chat-message-list";
import { Button } from "@/components/ui/button";
import { Send, Loader2 } from "lucide-react";
import { ChatSidebar, Contact } from "@/components/chat-sidebar";
import { ChatHeader } from "@/components/chat-header";
import { useState, useRef, useEffect, useCallback } from "react";
import { useChat } from "@/hooks/use-chat";
import { getCookie } from "@/lib/utils";

export default function Home() {
  const [currentUser, setCurrentUser] = useState<{ id: string; name: string; role: string } | null>(null);
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null); 
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isContactsLoading, setIsContactsLoading] = useState(true);

  // Handle updates to contacts from WebSocket or other events
  const updateContactsOnMessage = useCallback((newMessage: any) => {
    setContacts(prev => {
      // Find the contact who is relevant to this message
      const partnerId = newMessage.sender_id === currentUser?.id ? newMessage.recipient_id : newMessage.sender_id;
      
      const existingContact = prev.find(c => c.id === partnerId);
      if (!existingContact) return prev; // If not in contact list, ignore for now

      const updatedContact = {
        ...existingContact,
        lastMessage: newMessage.content,
        // Increment unread if message is incoming and not from currently selected chat
        unreadCount: (newMessage.sender_id === partnerId && selectedContact?.id !== partnerId) 
          ? (existingContact.unreadCount || 0) + 1 
          : existingContact.unreadCount
      };

      // Move to top and update
      return [updatedContact, ...prev.filter(c => c.id !== partnerId)];
    });
  }, [currentUser?.id, selectedContact?.id]);

  const { messages, sendMessage, isConnected, setMessages, isLoadingHistory } = useChat(
    selectedContact?.id || null, 
    currentUser?.id || null,
    updateContactsOnMessage
  );
  
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch current user on mount
  useEffect(() => {
    fetch("http://localhost:8000/me", {
      headers: {
        "Accept": "application/json",
      },
      credentials: 'include',
    })
      .then(res => {
        if (!res.ok) throw new Error("Not authenticated");
        return res.json();
      })
      .then(data => {
        if (data.user_id) {
          setCurrentUser({
            id: data.user_id,
            name: data.full_name,
            role: data.role_type
          });
        }
      })
      .catch(err => console.error("Failed to fetch user info", err));
  }, []);

  // Fetch contacts
  useEffect(() => {
    if (!currentUser) return;
    setIsContactsLoading(true);
    fetch("http://localhost:8000/chat/contacts/", {
      credentials: 'include',
    })
      .then(res => res.json())
      .then(data => {
        setContacts(data.contacts || []);
        setIsContactsLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch contacts", err);
        setIsContactsLoading(false);
      });
  }, [currentUser]);

  // Mark messages as read when contact is selected or new messages arrive while chat is open
  useEffect(() => {
    if (selectedContact?.id && isConnected) {
      fetch(`http://localhost:8000/chat/messages/${selectedContact.id}/read/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie('csrftoken') || "",
        },
        credentials: 'include',
      }).then(() => {
        // Also clear unread locally in the lifted contacts state
        setContacts(prev => prev.map(c => c.id === selectedContact.id ? { ...c, unreadCount: 0 } : c));
      }).catch(err => console.error("Failed to mark messages as read", err));
    }
  }, [selectedContact?.id, messages.length, isConnected]);

  const handleSendMessage = () => {
    if (inputValue.trim()) {
      sendMessage(inputValue);
      setInputValue("");
    }
  };

  const handleSelectChat = (contact: Contact) => {
    setSelectedContact(contact);
    setMessages([]); // Clear local messages when switching chat
  };

  useEffect(() => {
    if (!isLoadingHistory) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoadingHistory]);

  return (
    <main className="flex h-screen w-full bg-background overflow-hidden">
      
      {/* 1. LEFT SIDEBAR */}
      <ChatSidebar 
        onSelectChat={(id) => {}} 
        onSelectContact={handleSelectChat}
        currentUser={currentUser}
        selectedId={selectedContact?.id}
        contacts={contacts}
        loading={isContactsLoading}
      />

      {/* 2. MAIN CHAT AREA */}
      <div className="flex flex-1 flex-col h-full">
        
        {/* Chat Header */}
        <ChatHeader isConnected={isConnected} selectedContact={selectedContact} />

        {/* Chat Messages Area */}
        <div className="flex-1 overflow-hidden p-4 bg-gray-50/50">
          <ChatMessageList>
            {!currentUser && (
              <div className="text-center text-red-500 mt-10">
                You are not authenticated. Please log in to the main app.
              </div>
            )}
            {currentUser && !selectedContact && (
              <div className="text-center text-muted-foreground mt-10">
                Select a contact to start chatting.
              </div>
            )}
            {isLoadingHistory && (
              <div className="flex justify-center items-center py-10">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            )}
            {!isLoadingHistory && messages.length === 0 && selectedContact && (
              <div className="text-center text-muted-foreground mt-10">
                No messages yet. Start the conversation!
              </div>
            )}
            {messages.map((msg, index) => (
              <ChatBubble
                key={msg.id || index}
                variant={msg.role === "user" ? "sent" : "received"}
              >
                <ChatBubbleAvatar fallback={msg.sender_name?.[0] || "U"} />
                <ChatBubbleMessage
                  variant={msg.role === "user" ? "sent" : "received"}
                >
                  <div className="flex flex-col gap-1">
                    <span>{msg.content}</span>
                    <span className="text-[10px] opacity-70 self-end flex items-center gap-1">
                      {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      {msg.role === "user" && (
                        <span className="flex">
                          {msg.is_read ? (
                            <span className="text-blue-400">✓✓</span>
                          ) : msg.is_delivered ? (
                            <span>✓✓</span>
                          ) : (
                            <span>✓</span>
                          )}
                        </span>
                      )}
                    </span>
                  </div>
                </ChatBubbleMessage>
              </ChatBubble>
            ))}
            <div ref={messagesEndRef} />
          </ChatMessageList>
        </div>

        {/* Input Area */}
        <div className="p-4 border-t bg-background">
          <div className="flex gap-2 max-w-4xl mx-auto">
            <ChatInput 
              placeholder={!selectedContact ? "Select a contact first" : isConnected ? "Type your message..." : "Connecting to server..."} 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              disabled={!selectedContact}
            />
            <Button 
              size="icon" 
              className="shrink-0" 
              onClick={handleSendMessage} 
              disabled={!isConnected || !selectedContact || !inputValue.trim()}
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
        
      </div>
    </main>
  );
}