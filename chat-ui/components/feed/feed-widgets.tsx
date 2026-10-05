"use client";

import { useState, useEffect } from "react";
import { Gift, MoreHorizontal, Video, Search, Loader2 } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Contact {
  id: string;
  name: string;
  role: string;
  profile_photo: string | null;
  is_online: boolean;
}

interface FeedWidgetsProps {
  onContactClick: (contact: Contact) => void;
}

export function FeedWidgets({ onContactClick }: FeedWidgetsProps) {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    const fetchContacts = async () => {
      setIsLoading(true);
      try {
        const res = await fetch(`http://localhost:8001/chat/contacts/?q=${searchTerm}`, { credentials: 'include' });
        const data = await res.json();
        setContacts(data.contacts || []);
      } catch (err) {
        console.error("Failed to fetch contacts", err);
      } finally {
        setIsLoading(false);
      }
    };

    const timer = setTimeout(() => {
      fetchContacts();
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  const birthdays = [
    { name: "Sarah Connor", text: "and 2 others have birthdays today." }
  ];

  return (
    <div className="hidden lg:flex flex-col w-[280px] h-[calc(100vh-3.5rem)] sticky top-14 overflow-y-auto p-4 scrollbar-hide">
      
      {/* Sponsored */}
      <div className="mb-6">
        <h3 className="text-muted-foreground font-semibold text-sm mb-3 px-2">Sponsored</h3>
        <div className="flex items-center gap-3 p-2 cursor-pointer group hover:bg-muted/50 rounded-xl transition-colors">
          <div className="w-24 h-24 bg-muted rounded-xl overflow-hidden relative shrink-0">
             <div className="absolute inset-0 bg-primary/5 group-hover:bg-primary/10 transition-colors" />
             {/* Placeholder for center ad/info */}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-sm truncate">Summer Camp 2026</p>
            <p className="text-[10px] text-muted-foreground">Registration now open!</p>
          </div>
        </div>
      </div>

      <div className="h-px bg-border my-2 mx-2" />

      {/* Birthdays */}
      <div className="my-4">
        <h3 className="text-muted-foreground font-semibold text-sm mb-3 px-2">Birthdays</h3>
        <div className="flex items-center gap-3 cursor-pointer hover:bg-muted p-2 rounded-xl transition-colors">
          <Gift className="h-8 w-8 text-pink-500 shrink-0" />
          <div className="flex-1">
            <p className="text-xs leading-tight">
              <span className="font-bold">{birthdays[0].name}</span> {birthdays[0].text}
            </p>
          </div>
        </div>
      </div>

      <div className="h-px bg-border my-2 mx-2" />

      {/* Contacts / Staff */}
      <div className="my-4 flex-1">
        <div className="flex items-center justify-between mb-3 px-2">
          <h3 className="text-muted-foreground font-semibold text-sm">Contacts</h3>
          <div className="flex gap-1">
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-7 w-7 rounded-full"
              onClick={() => setShowSearch(!showSearch)}
            >
              <Search className="h-3.5 w-3.5 text-muted-foreground" />
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7 rounded-full">
              <MoreHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
            </Button>
          </div>
        </div>

        {showSearch && (
          <div className="px-2 mb-3 animate-in fade-in slide-in-from-top-1">
            <Input 
              placeholder="Search contacts..." 
              className="h-8 text-xs bg-muted/50 border-none rounded-full px-3 focus-visible:ring-1 focus-visible:ring-primary"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoFocus
            />
          </div>
        )}
        
        <div className="space-y-1">
          {isLoading && contacts.length === 0 ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            contacts.map((contact) => (
              <div 
                key={contact.id} 
                className="flex items-center gap-3 p-2 hover:bg-muted rounded-xl cursor-pointer transition-colors group"
                onClick={() => onContactClick(contact)}
              >
                <div className="relative shrink-0">
                  <Avatar className="h-9 w-9">
                    <AvatarImage src={contact.profile_photo || undefined} />
                    <AvatarFallback>{contact.name[0]}</AvatarFallback>
                  </Avatar>
                  {contact.is_online && (
                    <span className="absolute bottom-0.5 right-0.5 w-2.5 h-2.5 bg-green-500 border-2 border-background rounded-full" />
                  )}
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-sm font-medium truncate group-hover:text-primary transition-colors">{contact.name}</span>
                  <span className="text-[10px] text-muted-foreground uppercase tracking-tight">{contact.role.replace('_', ' ')}</span>
                </div>
              </div>
            ))
          )}
          
          {!isLoading && contacts.length === 0 && (
            <p className="text-center text-xs text-muted-foreground py-4 italic">No contacts found</p>
          )}
        </div>
      </div>

    </div>
  );
}
