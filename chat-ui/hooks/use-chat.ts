"use client";

import { useState, useEffect, useCallback, useRef } from "react";

export interface Message {
  id: string | number;
  sender_id: string;
  recipient_id?: string;
  sender_name: string;
  content: string;
  attachment?: string;
  attachment_type?: "image" | "video" | "file";
  timestamp: string;
  is_delivered?: boolean;
  is_read?: boolean;
  role?: "user" | "received"; 
}

export function useChat(
  recipientId: string | null, 
  currentUserId: string | null,
  onAnyMessageReceived?: (message: any) => void,
  onStatusUpdate?: (status: { user_id: string; is_online: boolean; last_seen?: string }) => void
) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Use refs for values needed in the onmessage handler to avoid closure staleness
  const recipientIdRef = useRef(recipientId);
  const currentUserIdRef = useRef(currentUserId);
  const onAnyMessageReceivedRef = useRef(onAnyMessageReceived);
  const onStatusUpdateRef = useRef(onStatusUpdate);

  useEffect(() => {
    recipientIdRef.current = recipientId;
    currentUserIdRef.current = currentUserId;
    onAnyMessageReceivedRef.current = onAnyMessageReceived;
    onStatusUpdateRef.current = onStatusUpdate;
  }, [recipientId, currentUserId, onAnyMessageReceived, onStatusUpdate]);

  // Fetch history when recipient changes
  useEffect(() => {
    if (!recipientId || !currentUserId) {
      setMessages([]);
      return;
    }

    setIsLoadingHistory(true);
    fetch(`http://localhost:8000/chat/messages/${recipientId}/`, {
      credentials: 'include',
    })
      .then(res => res.json())
      .then(data => {
        const history = data.messages.map((msg: any) => ({
          ...msg,
          role: msg.sender_id === currentUserId ? "user" : "received"
        }));
        setMessages(history);
        setIsLoadingHistory(false);
      })
      .catch(err => {
        console.error("Failed to fetch history", err);
        setIsLoadingHistory(false);
      });
  }, [recipientId, currentUserId]);

  useEffect(() => {
    if (isConnected && recipientId && socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: "mark_read",
        recipient_id: recipientId
      }));
    }
  }, [recipientId, isConnected]);

  const connectWebSocket = useCallback(() => {
    if (!currentUserIdRef.current) return;

    if (socketRef.current && (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    // Try localhost instead of localhost for better compatibility
    const socketUrl = `ws://localhost:8000/ws/chat/`;
    console.log("Connecting to WebSocket:", socketUrl);
    const socket = new WebSocket(socketUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log("Connected to chat WebSocket");
      setIsConnected(true);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      // Start ping interval to keep user online and detect disconnects
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      pingIntervalRef.current = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "ping" }));
        }
      }, 10000); // Ping every 10 seconds

      // Mark as read immediately on connect if a recipient is selected
      if (recipientIdRef.current) {
        socket.send(JSON.stringify({
          type: "mark_read",
          recipient_id: recipientIdRef.current
        }));
      }
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("WebSocket message received:", data);
      
      if (data.type === "chat_message") {
        const newMessage = data.message;
        const curRecipientId = recipientIdRef.current;
        const curUserId = currentUserIdRef.current;

        newMessage.role = newMessage.sender_id === curUserId ? "user" : "received";
        
        // Notify parent about ANY received message (for sidebar)
        onAnyMessageReceivedRef.current?.(newMessage);

        // ONLY append to messages if it belongs to the current conversation
        const isFromMeToHim = newMessage.sender_id === curUserId && newMessage.recipient_id === curRecipientId;
        const isFromHimToMe = newMessage.sender_id === curRecipientId && newMessage.recipient_id === curUserId;

        if (isFromMeToHim || isFromHimToMe) {
          if (isFromHimToMe && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
              type: "mark_read",
              recipient_id: curRecipientId
            }));
          }
          setMessages((prev) => {
            // Prevent duplicates (e.g. from same-sender broadcast)
            if (prev.some(m => m.id === newMessage.id)) return prev;
            return [...prev, newMessage];
          });
        }
      } else if (data.type === "messages_delivered") {
        if (data.recipient_id === recipientIdRef.current) {
          setMessages(prev => prev.map(msg => 
            msg.role === "user" ? { ...msg, is_delivered: true } : msg
          ));
        }
      } else if (data.type === "messages_read") {
        if (data.recipient_id === recipientIdRef.current) {
          setMessages(prev => prev.map(msg => 
            msg.role === "user" ? { ...msg, is_read: true, is_delivered: true } : msg
          ));
        }
      } else if (data.type === "online_status") {
        onStatusUpdateRef.current?.({
          user_id: data.user_id,
          is_online: data.is_online,
          last_seen: data.last_seen
        });
      }
    };

    socket.onclose = (e) => {
      console.log("Disconnected from chat WebSocket", e.reason);
      setIsConnected(false);
      
      // Clear ping interval on disconnect
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
      
      // Attempt to reconnect after 3 seconds if still authenticated
      if (!reconnectTimeoutRef.current && currentUserIdRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectTimeoutRef.current = null;
          connectWebSocket();
        }, 3000);
      }
    };

    socket.onerror = (err) => {
      console.error("WebSocket error", err);
      // Let onclose handle reconnection
    };
  }, []); // Static connect function

  useEffect(() => {
    if (currentUserId) {
      connectWebSocket();
    }

    return () => {
      // Don't close on every render, only on unmount
    };
  }, [currentUserId, connectWebSocket]);

  // Handle cleanup on unmount
  useEffect(() => {
    return () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  const sendMessage = useCallback((content: string) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN && recipientId) {
      socketRef.current.send(
        JSON.stringify({
          type: "chat_message",
          recipient_id: recipientId,
          content: content,
        })
      );
    }
  }, [recipientId]);

  const sendJson = useCallback((data: any) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(data));
    }
  }, []);

  const sendFile = useCallback(async (file: File, content: string = "") => {
    if (!recipientId) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("recipient_id", recipientId);
    formData.append("content", content);
    
    let type: "image" | "video" | "file" = "file";
    if (file.type.startsWith("image/")) type = "image";
    else if (file.type.startsWith("video/")) type = "video";
    
    formData.append("attachment_type", type);

    const getCookie = (name: string) => {
      let cookieValue = null;
      if (typeof document !== 'undefined' && document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    };

    try {
      const response = await fetch("http://localhost:8000/chat/upload/", {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": getCookie('csrftoken') || "",
        },
        credentials: 'include',
      });
      
      if (!response.ok) throw new Error("Upload failed");
      
      const data = await response.json();
      return data.message;
    } catch (error) {
      console.error("Error sending file:", error);
      throw error;
    }
  }, [recipientId]);

  return { messages, sendMessage, sendJson, sendFile, isConnected, setMessages, isLoadingHistory };
}
