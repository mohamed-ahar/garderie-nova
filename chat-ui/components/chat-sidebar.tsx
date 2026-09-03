"use client";

import { MessageSquare, Plus, Search, Settings, UserPlus, Inbox, Ban } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useState, useEffect } from "react";
import { UserSearchDialog } from "./user-search-dialog";
import { InvitationsDialog } from "./invitations-dialog";
import { BlockedUsersDialog } from "./blocked-users-dialog";

export interface Contact {
  id: string;
  name: string;
  role: string;
  avatar: string;
  lastMessage?: string;
  time?: string;
  unreadCount?: number;
}

interface ChatSidebarProps {
  onSelectChat?: (id: string) => void;
  onSelectContact?: (contact: Contact) => void;
  currentUser?: { name: string; id: string; role: string } | null;
  selectedId?: string | null;
  contacts: Contact[];
  loading: boolean;
  onRefreshContacts?: () => void;
}

export function ChatSidebar({ onSelectChat, onSelectContact, currentUser, selectedId, contacts, loading, onRefreshContacts }: ChatSidebarProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isInvitesOpen, setIsInvitesOpen] = useState(false);
  const [isBlockedOpen, setIsBlockedOpen] = useState(false);
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    const fetchPending = async () => {
      try {
        const res = await fetch("http://localhost:8000/chat/invitations/", { credentials: 'include' });
        const data = await res.json();
        setPendingCount(data.received.length);
      } catch (err) { }
    };
    fetchPending();
    const interval = setInterval(fetchPending, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const filteredContacts = contacts.filter(c => 
    c.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full w-80 border-r bg-muted/20">
      
      {/* Sidebar Header */}
      <div className="p-4 border-b flex items-center justify-between sticky top-0 bg-background z-10">
        <h2 className="font-semibold text-lg tracking-tight">Messages</h2>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" className="relative" onClick={() => setIsInvitesOpen(true)} title="Invitations">
            <Inbox className="h-5 w-5" />
            {pendingCount > 0 && (
              <span className="absolute top-1 right-1 flex h-3 w-3 items-center justify-center rounded-full bg-primary text-[8px] font-bold text-primary-foreground">
                {pendingCount}
              </span>
            )}
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setIsSearchOpen(true)} title="Find People">
            <UserPlus className="h-5 w-5" />
          </Button>
        </div>
      </div>

      <UserSearchDialog isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
      <InvitationsDialog 
        isOpen={isInvitesOpen} 
        onClose={() => setIsInvitesOpen(false)} 
        onActionSuccess={() => {
          onRefreshContacts?.();
          setPendingCount(prev => Math.max(0, prev - 1));
        }}
      />
      <BlockedUsersDialog 
        isOpen={isBlockedOpen} 
        onClose={() => setIsBlockedOpen(false)} 
        onUnblockSuccess={onRefreshContacts}
      />

      {/* Search Bar */}
      <div className="p-4">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search contacts..." 
            className="pl-8 bg-background" 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Chat List */}
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-1 p-2">
          {loading ? (
            <div className="p-4 text-center text-sm text-muted-foreground">Loading contacts...</div>
          ) : filteredContacts.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground">No contacts found</div>
          ) : (
            filteredContacts.map((chat) => (
              <button
                key={chat.id}
                onClick={() => {
                  onSelectChat?.(chat.id);
                  onSelectContact?.(chat);
                }}
                className={`flex items-start gap-3 rounded-lg px-3 py-3 text-left transition-all hover:bg-accent ${selectedId === chat.id ? 'bg-accent font-medium' : ''}`}
              >
                <div className="relative">
                  <Avatar>
                    <AvatarFallback>{chat.avatar}</AvatarFallback>
                  </Avatar>
                  {chat.unreadCount && chat.unreadCount > 0 && selectedId !== chat.id && (
                    <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
                      {chat.unreadCount}
                    </span>
                  )}
                </div>
                <div className="flex w-full flex-col overflow-hidden">
                  <div className="flex items-center justify-between">
                    <span className={`text-sm truncate ${chat.unreadCount && chat.unreadCount > 0 ? 'font-bold' : 'font-medium'}`}>
                      {chat.name}
                    </span>
                    <span className="text-[10px] text-muted-foreground uppercase shrink-0">{chat.role}</span>
                  </div>
                  <span className={`truncate text-xs ${chat.unreadCount && chat.unreadCount > 0 ? 'font-semibold text-foreground' : 'text-muted-foreground'}`}>
                    {chat.lastMessage || "Start a conversation"}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>
      </ScrollArea>

      {/* User Footer */}
      <div className="p-4 border-t flex items-center justify-between bg-background">
        <div className="flex items-center gap-2 overflow-hidden">
          <Avatar className="h-8 w-8 shrink-0">
            <AvatarFallback>{currentUser?.name?.[0] || "ME"}</AvatarFallback>
          </Avatar>
          <div className="flex flex-col min-w-0">
            <div className="text-sm font-semibold truncate">{currentUser?.name || "My Account"}</div>
            <div className="text-[10px] text-muted-foreground uppercase truncate">{currentUser?.role}</div>
          </div>
        </div>
        <Button variant="ghost" size="icon" className="shrink-0" onClick={() => setIsBlockedOpen(true)} title="Blocked Users">
          <Ban className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}