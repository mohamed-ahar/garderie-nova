"use client";

import { useEffect, useState } from "react";
import { FeedLayout } from "@/components/feed/feed-layout";
import { FeedSidebar } from "@/components/feed/feed-sidebar";
import { FeedWidgets } from "@/components/feed/feed-widgets";
import { FeedStream } from "@/components/feed/feed-stream";
import { PushNotificationPrompt } from "@/components/push-notification-prompt";

export default function FeedPage() {
  const [currentUser, setCurrentUser] = useState<{ id: string; name: string; role: string; profile_photo?: string | null } | null>(null);
  const [currentFilter, setCurrentFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewAuthorId, setViewAuthorId] = useState<string | null>(null);

  const handleOpenChat = (contactId: string) => {
    // Open in a named new tab. If 'GarderieNovaChat' exists, it will be focused/navigated.
    if (typeof window !== 'undefined') {
      window.open(`/?chat=${contactId}`, "GarderieNovaChat");
    }
  };

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

  if (!currentUser) return null;

  return (
    <>
      <FeedLayout currentUser={currentUser} onSearch={setSearchQuery}>
        <FeedSidebar 
          currentUser={currentUser} 
          currentFilter={currentFilter} 
          onFilterChange={(f) => {
            setCurrentFilter(f);
            setViewAuthorId(null);
          }} 
        />
        <div className="flex-1 max-w-[680px] w-full min-w-0">
          <FeedStream 
            currentUser={currentUser} 
            filter={currentFilter} 
            searchQuery={searchQuery}
            authorId={viewAuthorId || undefined}
            onPersonClick={(user) => setViewAuthorId(user.id)}
            onBack={() => setViewAuthorId(null)}
          />
        </div>
        <FeedWidgets onContactClick={(contact) => handleOpenChat(contact.id)} />
      </FeedLayout>

      <PushNotificationPrompt />
    </>
  );
}
