"use client";

import {
  ChatBubble,
  ChatBubbleAvatar,
  ChatBubbleMessage,
} from "@/components/ui/chat/chat-bubble";
import { ChatInput } from "@/components/ui/chat/chat-input";
import { ChatMessageList } from "@/components/ui/chat/chat-message-list";
import { Button } from "@/components/ui/button";
import { Send, Loader2, Sparkles, Check, CheckCheck, File, Image as ImageIcon, Video as VideoIcon } from "lucide-react";
import { ChatSidebar, Contact } from "@/components/chat-sidebar";
import { ChatHeader } from "@/components/chat-header";
import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { useChat } from "@/hooks/use-chat";
import { getCookie } from "@/lib/utils";
import { MediaPreview } from "@/components/media-preview";

export default function Home() {
  const [currentUser, setCurrentUser] = useState<{ id: string; name: string; role: string } | null>(null);
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isContactsLoading, setIsContactsLoading] = useState(true);
  
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [currentMediaIndex, setCurrentMediaIndex] = useState(0);

  const imageInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle updates to contacts from WebSocket or other events
  const updateContactsOnMessage = useCallback((newMessage: any) => {
    setContacts(prev => {
      const partnerId = newMessage.sender_id === currentUser?.id ? newMessage.recipient_id : newMessage.sender_id;

      const existingContact = prev.find(c => c.id === partnerId);
      if (!existingContact) return prev;

      const updatedContact = {
        ...existingContact,
        lastMessage: newMessage.attachment_type ? `Sent an ${newMessage.attachment_type}` : newMessage.content,
        unreadCount: (newMessage.sender_id === partnerId && selectedContact?.id !== partnerId)
          ? (existingContact.unreadCount || 0) + 1
          : existingContact.unreadCount
      };

      return [updatedContact, ...prev.filter(c => c.id !== partnerId)];
    });
  }, [currentUser?.id, selectedContact?.id]);

  const { messages, sendMessage, sendFile, isConnected, setMessages, isLoadingHistory } = useChat(
    selectedContact?.id || null,
    currentUser?.id || null,
    updateContactsOnMessage
  );

  const [inputValue, setInputValue] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Extract media items for the preview
  const mediaList = useMemo(() => {
    return messages
      .filter(msg => msg.attachment && (msg.attachment_type === "image" || msg.attachment_type === "video"))
      .map(msg => ({
        url: msg.attachment!,
        type: msg.attachment_type as "image" | "video",
        id: msg.id
      }));
  }, [messages]);

  const openPreview = (messageId: string | number) => {
    const index = mediaList.findIndex(m => m.id === messageId);
    if (index !== -1) {
      setCurrentMediaIndex(index);
      setIsPreviewOpen(true);
    }
  };

  useEffect(() => {
    fetch("http://localhost:8000/me", {
      headers: { "Accept": "application/json" },
      credentials: 'include',
    })
      .then(res => {
        if (!res.ok) {
          // Redirect to backend login with 'next' pointing back to this chat app
          const chatAppUrl = encodeURIComponent(window.location.origin);
          window.location.href = `http://localhost:8000/?next=${chatAppUrl}`;
          throw new Error("Not authenticated");
        }
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

  const fetchContacts = useCallback(() => {
    if (!currentUser) return;
    setIsContactsLoading(true);
    fetch("http://localhost:8000/chat/contacts/", { credentials: 'include' })
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

  useEffect(() => {
    fetchContacts();
  }, [fetchContacts]);

  useEffect(() => {
    if (selectedContact?.id && isConnected) {
      fetch(`http://localhost:8000/chat/messages/${selectedContact.id}/read/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie('csrftoken') || "" },
        credentials: 'include',
      }).then(() => {
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

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && selectedContact) {
      setIsUploading(true);
      try {
        await sendFile(file, inputValue);
        setInputValue("");
        e.target.value = "";
      } catch (err) {
        console.error("Failed to send file", err);
      } finally {
        setIsUploading(false);
      }
    }
  };

  const handleSelectChat = (contact: Contact) => {
    setSelectedContact(contact);
    setMessages([]);
  };

  useEffect(() => {
    if (!isLoadingHistory) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoadingHistory]);

  return (
    // Updated container: using bg-muted/20 to give a slight contrast to the white chat area
    <main className="flex h-screen w-full bg-muted/20 overflow-hidden font-sans">

      {/* 1. LEFT SIDEBAR - The sidebar component should automatically pick up the 'dark' sidebar vars from globals.css */}
      <ChatSidebar
        onSelectChat={(id) => { }}
        onSelectContact={handleSelectChat}
        currentUser={currentUser}
        selectedId={selectedContact?.id}
        contacts={contacts}
        loading={isContactsLoading}
        onRefreshContacts={fetchContacts}
      />

      {/* 2. MAIN CONTENT AREA */}
      <div className="flex flex-1 flex-col h-full relative">

        {/* Top Decorative Header (Optional, mimics the dashboard header space) */}
        {!selectedContact && currentUser && (
          <div className="absolute top-8 left-8 right-8 z-0 opacity-50 pointer-events-none">
            <h1 className="text-4xl font-bold tracking-tight text-foreground">
              Welcome back, <br />
              <span className="text-primary">{currentUser.name}</span>.
            </h1>
            <p className="text-muted-foreground mt-2">
              Select a contact from the sidebar to start communication.
            </p>
          </div>
        )}

        {/* Chat Wrapper - styled as a 'Card' floating in the space if desired, or full height */}
        <div className="flex flex-1 flex-col h-full z-10 bg-background/50 backdrop-blur-sm">

          {/* Chat Header */}
          {selectedContact && (
            <div className="bg-background border-b px-4 h-16 flex items-center shadow-sm shrink-0">
              <ChatHeader 
                isConnected={isConnected} 
                selectedContact={selectedContact} 
                onBlockUpdate={() => {
                  fetchContacts();
                  setSelectedContact(null);
                }}
              />
            </div>
          )}

          {/* Chat Messages Area */}
          <div className="flex-1 overflow-hidden p-4 md:p-6 bg-transparent">
            <ChatMessageList>
              {!currentUser && (
                <div className="flex flex-col items-center justify-center h-full text-destructive space-y-2">
                  <p>You are not authenticated.</p>
                </div>
              )}
              {currentUser && !selectedContact && (
                // Empty state filler
                <div className="h-full" />
              )}
              {isLoadingHistory && (
                <div className="flex justify-center items-center h-full">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              )}
              {!isLoadingHistory && messages.length === 0 && selectedContact && (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground space-y-4">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                    <Sparkles className="w-6 h-6 text-primary" />
                  </div>
                  <p>No messages yet. Start the conversation!</p>
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
                    className={msg.role === "user" ? "bg-primary text-primary-foreground shadow-md" : "bg-white border shadow-sm"}
                  >
                    <div className="flex flex-col gap-2">
                      {msg.attachment && (
                        <div className="max-w-xs md:max-w-md rounded-lg overflow-hidden mb-1">
                          {msg.attachment_type === "image" && (
                            <img 
                              src={msg.attachment} 
                              alt="Attachment" 
                              className="w-full h-auto object-cover max-h-60 cursor-pointer hover:opacity-90 transition-opacity" 
                              onClick={() => openPreview(msg.id)}
                            />
                          )}
                          {msg.attachment_type === "video" && (
                            <div className="relative group cursor-pointer" onClick={() => openPreview(msg.id)}>
                              <video src={msg.attachment} className="w-full h-auto max-h-60" />
                              <div className="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/30 transition-colors">
                                <VideoIcon className="w-12 h-12 text-white/80" />
                              </div>
                            </div>
                          )}
                          {msg.attachment_type === "file" && (
                            <a 
                              href={msg.attachment} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="flex items-center gap-2 p-2 bg-muted/20 rounded hover:bg-muted/30 transition-colors underline"
                            >
                              <File className="w-4 h-4" />
                              <span className="text-xs truncate">Download File</span>
                            </a>
                          )}
                        </div>
                      )}
                      {msg.content && <span>{msg.content}</span>}
                      <span className="text-[10px] opacity-70 self-end flex items-center gap-1">
                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}

                        {msg.role === "user" && (
                          <span className="flex items-center gap-0.5 ml-1">
                            {msg.is_read ? (
                              // READ: Double tick, Solid White
                              <CheckCheck className="w-3.5 h-3.5 text-white" strokeWidth={3} />
                            ) : msg.is_delivered ? (
                              // DELIVERED: Double tick, Faded (50% opacity)
                              <CheckCheck className="w-3.5 h-3.5 text-white/50" />
                            ) : (
                              // SENT: Single tick, Faded (50% opacity)
                              <Check className="w-3.5 h-3.5 text-white/50" />
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

          {/* Input Area - Floats slightly at the bottom */}
          <div className="p-4 bg-background border-t">
            <div className="flex gap-2 max-w-4xl mx-auto items-end">
              <input 
                type="file" 
                ref={imageInputRef} 
                className="hidden" 
                accept="image/*"
                onChange={handleFileSelect}
              />
              <input 
                type="file" 
                ref={videoInputRef} 
                className="hidden" 
                accept="video/*"
                onChange={handleFileSelect}
              />
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                onChange={handleFileSelect}
              />

              <div className="flex gap-1 mb-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="shrink-0 h-10 w-10 rounded-full text-muted-foreground hover:text-primary transition-colors"
                  onClick={() => imageInputRef.current?.click()}
                  disabled={!selectedContact || isUploading}
                  title="Send Image"
                >
                  <ImageIcon className="w-5 h-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="shrink-0 h-10 w-10 rounded-full text-muted-foreground hover:text-primary transition-colors"
                  onClick={() => videoInputRef.current?.click()}
                  disabled={!selectedContact || isUploading}
                  title="Send Video"
                >
                  <VideoIcon className="w-5 h-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="shrink-0 h-10 w-10 rounded-full text-muted-foreground hover:text-primary transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={!selectedContact || isUploading}
                  title="Send File"
                >
                  <File className="w-5 h-5" />
                </Button>
              </div>

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
                className="min-h-[50px] bg-muted/30 border-0 focus-visible:ring-1 focus-visible:ring-primary rounded-xl px-4 py-3"
              />
              <Button
                size="icon"
                className="shrink-0 h-[50px] w-[50px] rounded-xl bg-primary hover:bg-primary/90 shadow-md transition-all hover:scale-105"
                onClick={handleSendMessage}
                disabled={!isConnected || !selectedContact || (!inputValue.trim() && !isUploading)}
              >
                {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Media Preview Overlay */}
      <MediaPreview
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        mediaItems={mediaList}
        currentIndex={currentMediaIndex}
        onIndexChange={setCurrentMediaIndex}
      />
    </main>
  );
}
