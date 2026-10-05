"use client";

import { useEffect, useState } from "react";
import { FeedLayout } from "@/components/feed/feed-layout";
import { FeedSidebar } from "@/components/feed/feed-sidebar";
import { FeedWidgets } from "@/components/feed/feed-widgets";
import { FeedStream } from "@/components/feed/feed-stream";
import { ChatBoxesContainer } from "@/components/feed/chat-boxes-container";
import { PushNotificationPrompt } from "@/components/push-notification-prompt";

export default function FeedPage() {
  const [currentUser, setCurrentUser] = useState<{ id: string; name: string; role: string; profile_photo?: string | null } | null>(null);
  const [currentFilter, setCurrentFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [openChats, setOpenChats] = useState<any[]>([]);

  useEffect(() => {
    fetch("http://localhost:8001/me", {
      headers: { "Accept": "application/json" },
      credentials: 'include',
    })
      .then(res => {
        if (!res.ok) {
           const chatAppUrl = encodeURIComponent(window.location.origin);
           window.location.href = `http://localhost:8001/?next=${chatAppUrl}`;
           throw new Error("Not authenticated");
        }
        return res.json();
      })
      .then(data => {
        if (data.user_id) {
          setCurrentUser({
            id: data.user_id,
            name: data.full_name,
            role: data.role_type,
            profile_photo: data.profile_photo ? `http://localhost:8001${data.profile_photo}` : null
          });
        }
      })
      .catch(err => console.error("Failed to fetch user info", err));
  }, []);

  const handleOpenChat = (contact: any) => {
    setOpenChats(prev => {
      if (prev.some(c => c.id === contact.id)) return prev;
      return [contact, ...prev].slice(0, 3);
    });
  };

  const handleCloseChat = (contactId: string) => {
    setOpenChats(prev => prev.filter(c => c.id !== contactId));
  };

  if (!currentUser) return null;

  return (
    <>
      <FeedLayout currentUser={currentUser} onSearch={setSearchQuery}>
        <FeedSidebar 
          currentUser={currentUser} 
          currentFilter={currentFilter} 
          onFilterChange={setCurrentFilter} 
        />
        <div className="flex-1 max-w-[680px] w-full min-w-0">
          <FeedStream 
            currentUser={currentUser} 
            filter={currentFilter} 
            searchQuery={searchQuery}
            onPersonClick={handleOpenChat}
          />
        </div>
        <FeedWidgets onContactClick={handleOpenChat} />
      </FeedLayout>

      <ChatBoxesContainer 
        openChats={openChats}
        currentUserId={currentUser.id}
        currentUser={currentUser}
        onCloseChat={handleCloseChat}
      />

      <PushNotificationPrompt />
    </>
  );
}
