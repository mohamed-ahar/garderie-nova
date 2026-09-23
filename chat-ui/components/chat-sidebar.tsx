"use client";

import { MessageSquare, Plus, Search, Settings, Filter, FilterX } from "lucide-react";

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

}



type FilterRole = "all" | "director" | "educator" | "parent";



export function ChatSidebar({ onSelectChat, onSelectContact, currentUser, selectedId, contacts, loading, onRefreshContacts }: ChatSidebarProps) {

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

      

      {/* Sidebar Header */}

      <div className="p-4 border-b flex items-center justify-between sticky top-0 bg-background z-10">

        <h2 className="font-semibold text-lg tracking-tight">Messages</h2>

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


