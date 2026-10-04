"use client";

import { MessageSquare, Plus, Search, Settings, Filter, FilterX, LayoutGrid, Bell, Image as ImageIcon, Calendar, FileText, Video } from "lucide-react";

import { Button } from "@/components/ui/button";

import { Input } from "@/components/ui/input";

import { ScrollArea } from "@/components/ui/scroll-area";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

import { useState, useEffect } from "react";

import { UserSearchDialog } from "./user-search-dialog";

import { cn } from "@/lib/utils";



export interface Contact {

  id: string;

  name: string;

  role: string;

  avatar: string;

  profile_photo?: string | null;

  lastMessage?: string;

  time?: string;

  unreadCount?: number;

  is_online?: boolean;

  last_seen?: string;

}



interface ChatSidebarProps {

  onSelectChat?: (id: string) => void;

  onSelectContact?: (contact: Contact) => void;

  currentUser?: { name: string; id: string; role: string; profile_photo?: string | null } | null;

  selectedId?: string | null;

  contacts: Contact[];

  loading: boolean;

  onRefreshContacts?: () => void;
  activeView?: "chat" | "feed";
  onViewChange?: (view: "chat" | "feed") => void;
  activeFeedFilter?: string;
  onFeedFilterChange?: (filter: string) => void;

}



type FilterRole = "all" | "director" | "educator" | "parent";



export function ChatSidebar({ onSelectChat, onSelectContact, currentUser, selectedId, contacts, loading, onRefreshContacts, activeView = "chat", onViewChange, activeFeedFilter = "all", onFeedFilterChange }: ChatSidebarProps) {

  const [searchTerm, setSearchTerm] = useState("");

  const [isSearchOpen, setIsSearchOpen] = useState(false);

  const [activeTab, setActiveTab] = useState<FilterRole>("all");

  const [isFilterEnabled, setIsFilterEnabled] = useState(true);

  const filteredContacts = contacts.filter(c => {

    const matchesSearch = c.name.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesRole = !isFilterEnabled || activeTab === "all" || c.role === activeTab;

    return matchesSearch && matchesRole;

  });



  const tabs: { id: FilterRole; label: string }[] = [

    { id: "all", label: "All" },

    { id: "director", label: "Directors" },

    { id: "educator", label: "Staff" },

    { id: "parent", label: "Parents" },

  ];



  return (

    <div className="flex flex-col h-full w-80 border-r bg-muted/20">

      {/* View Switcher Tabs */}
      <div className="flex p-2 gap-2 bg-background border-b shrink-0">
        <Button 
          variant={activeView === "chat" ? "default" : "ghost"} 
          className={cn("flex-1 h-10 gap-2 font-bold uppercase tracking-widest text-[10px]", activeView === "chat" ? "shadow-md" : "")}
          onClick={() => onViewChange?.("chat")}
        >
          <MessageSquare className="h-4 w-4" />
          Messages
        </Button>
        <Button 
          variant={activeView === "feed" ? "default" : "ghost"} 
          className={cn("flex-1 h-10 gap-2 font-bold uppercase tracking-widest text-[10px]", activeView === "feed" ? "shadow-md" : "")}
          onClick={() => onViewChange?.("feed")}
        >
          <LayoutGrid className="h-4 w-4" />
          Center Feed
        </Button>
      </div>

      {activeView === "chat" && (
        <>
          {/* Sidebar Header */}
          <div className="p-4 border-b flex items-center justify-between sticky top-0 bg-background z-10">
            <h2 className="font-semibold text-lg tracking-tight">Direct Chats</h2>

        <div className="flex gap-1">

          <Button 

            variant="ghost" 

            size="icon" 

            onClick={() => setIsFilterEnabled(!isFilterEnabled)} 

            title={isFilterEnabled ? "Disable Filter" : "Enable Filter"}

            className={cn(isFilterEnabled ? "text-primary" : "text-muted-foreground")}

          >

            {isFilterEnabled ? <Filter className="h-5 w-5" /> : <FilterX className="h-5 w-5" />}

          </Button>

          <Button variant="ghost" size="icon" onClick={() => setIsSearchOpen(true)} title="Find People">

            <Search className="h-5 w-5" />

          </Button>

        </div>

      </div>



      <UserSearchDialog 

        isOpen={isSearchOpen} 

        onClose={() => setIsSearchOpen(false)} 

        onSelectUser={(user) => onSelectContact?.(user)}

      />



      {/* Tabs */}

      {isFilterEnabled && (

        <div className="flex p-1 gap-1 bg-muted/50 border-b overflow-x-auto no-scrollbar">

          {tabs.map((tab) => (

            <button

              key={tab.id}

              onClick={() => setActiveTab(tab.id)}

              className={cn(

                "px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider rounded-md transition-all whitespace-nowrap",

                activeTab === tab.id 

                  ? "bg-background text-primary shadow-sm" 

                  : "text-muted-foreground hover:bg-background/50"

              )}

            >

              {tab.label}

            </button>

          ))}

        </div>

      )}



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

      <ScrollArea className="flex-1 overflow-y-auto">

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

                    <AvatarImage src={chat.profile_photo || undefined} className="object-cover" />

                    <AvatarFallback>{chat.avatar}</AvatarFallback>

                  </Avatar>

                  {/* Online indicator */}

                  {chat.is_online && (

                    <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background bg-green-500" />

                  )}

                  {chat.unreadCount! > 0 && selectedId !== chat.id && (

                    <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">

                      {chat.unreadCount}

                    </span>

                  )}

                </div>

                <div className="flex w-full flex-col overflow-hidden">

                  <div className="flex items-center justify-between">

                    <span className={`text-sm truncate ${(chat.unreadCount ?? 0) > 0 ? 'font-bold' : 'font-medium'}`}>

                      {chat.name}

                    </span>

                    <span className="text-[10px] text-muted-foreground uppercase shrink-0">{chat.role}</span>

                  </div>

                  <span className={`truncate text-xs ${(chat.unreadCount ?? 0) > 0 ? 'font-semibold text-foreground' : 'text-muted-foreground'}`}>

                    {chat.lastMessage || "Start a conversation"}

                  </span>

                </div>

              </button>

            ))

          )}

        </div>
      </ScrollArea>
      </>
      )}

      {activeView === "feed" && (
        <div className="flex-1 flex flex-col bg-background">
          <div className="p-4 border-b">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-4">Quick Filters</h3>
            <div className="space-y-1">
              <Button 
                variant={activeFeedFilter === "all" ? "secondary" : "ghost"} 
                onClick={() => onFeedFilterChange?.("all")}
                className={cn("w-full justify-start gap-3 h-11 px-4 rounded-xl text-sm", activeFeedFilter === "all" ? "shadow-sm border-0 font-semibold" : "font-medium text-muted-foreground hover:text-foreground")}
              >
                <LayoutGrid className={cn("h-4 w-4", activeFeedFilter === "all" ? "text-primary" : "")} />
                All Updates
              </Button>
              <Button 
                variant={activeFeedFilter === "announcements" ? "secondary" : "ghost"} 
                onClick={() => onFeedFilterChange?.("announcements")}
                className={cn("w-full justify-start gap-3 h-11 px-4 rounded-xl text-sm", activeFeedFilter === "announcements" ? "shadow-sm border-0 font-semibold" : "font-medium text-muted-foreground hover:text-foreground")}
              >
                <Bell className={cn("h-4 w-4", activeFeedFilter === "announcements" ? "text-primary" : "")} />
                Announcements
              </Button>
              <Button 
                variant={activeFeedFilter === "photos" ? "secondary" : "ghost"} 
                onClick={() => onFeedFilterChange?.("photos")}
                className={cn("w-full justify-start gap-3 h-11 px-4 rounded-xl text-sm", activeFeedFilter === "photos" ? "shadow-sm border-0 font-semibold" : "font-medium text-muted-foreground hover:text-foreground")}
              >
                <ImageIcon className={cn("h-4 w-4", activeFeedFilter === "photos" ? "text-primary" : "")} />
                Photos
              </Button>
              <Button 
                variant={activeFeedFilter === "videos" ? "secondary" : "ghost"} 
                onClick={() => onFeedFilterChange?.("videos")}
                className={cn("w-full justify-start gap-3 h-11 px-4 rounded-xl text-sm", activeFeedFilter === "videos" ? "shadow-sm border-0 font-semibold" : "font-medium text-muted-foreground hover:text-foreground")}
              >
                <Video className={cn("h-4 w-4", activeFeedFilter === "videos" ? "text-primary" : "")} />
                Videos
              </Button>
              <Button 
                variant={activeFeedFilter === "events" ? "secondary" : "ghost"} 
                onClick={() => onFeedFilterChange?.("events")}
                className={cn("w-full justify-start gap-3 h-11 px-4 rounded-xl text-sm", activeFeedFilter === "events" ? "shadow-sm border-0 font-semibold" : "font-medium text-muted-foreground hover:text-foreground")}
              >
                <Calendar className={cn("h-4 w-4", activeFeedFilter === "events" ? "text-primary" : "")} />
                Events
              </Button>
            </div>
          </div>

          <div className="p-4">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-4">Resources</h3>
            <div className="p-4 rounded-2xl bg-muted/30 border border-dashed flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-background flex items-center justify-center border shadow-sm">
                  <FileText className="h-4 w-4 text-primary" />
                </div>
                <div className="flex-1 overflow-hidden">
                  <div className="text-xs font-bold truncate">Center Documents</div>
                  <div className="text-[10px] text-muted-foreground">Rules & Policies</div>
                </div>
              </div>
              <Button variant="outline" size="sm" className="w-full rounded-xl text-[10px] font-bold h-8 uppercase tracking-wider">View Files</Button>
            </div>
          </div>

          <div className="mt-auto p-6 text-center">
            <p className="text-[10px] text-muted-foreground leading-relaxed">
              Stay updated with the latest news and announcements from your center.
            </p>
          </div>
        </div>
      )}

      {/* User Footer */}

      <div className="p-4 border-t flex items-center justify-between bg-background">

        <div className="flex items-center gap-2 overflow-hidden">

          <Avatar className="h-8 w-8 shrink-0">

            <AvatarImage src={currentUser?.profile_photo || undefined} className="object-cover" />

            <AvatarFallback>{currentUser?.name?.[0] || "ME"}</AvatarFallback>

          </Avatar>

          <div className="flex flex-col min-w-0">

            <div className="text-sm font-semibold truncate">{currentUser?.name || "My Account"}</div>

            <div className="text-[10px] text-muted-foreground uppercase truncate">{currentUser?.role}</div>

          </div>

        </div>

      </div>

    </div>

  );

}


