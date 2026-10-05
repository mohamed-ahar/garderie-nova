"use client";

import { LayoutGrid, Bell, ImageIcon, Video, Calendar, Users, Bookmark, Clock, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface FeedSidebarProps {
  currentUser: any;
  currentFilter: string;
  onFilterChange: (filter: string) => void;
}

export function FeedSidebar({ currentUser, currentFilter, onFilterChange }: FeedSidebarProps) {
  const menuItems = [
    { id: "all", label: "News Feed", icon: LayoutGrid, color: "text-primary" },
    { id: "announcements", label: "Announcements", icon: Bell, color: "text-amber-500" },
    { id: "photos", label: "Photos", icon: ImageIcon, color: "text-emerald-500" },
    { id: "videos", label: "Videos", icon: Video, color: "text-blue-500" },
    { id: "events", label: "Events", icon: Calendar, color: "text-rose-500" },
  ];

  const shortcuts = [
    { label: "Staff Room", icon: Users },
    { label: "Saved Posts", icon: Bookmark },
    { label: "Memories", icon: Clock },
  ];

  return (
    <div className="hidden lg:flex flex-col w-[280px] h-[calc(100vh-3.5rem)] sticky top-14 overflow-y-auto p-4 scrollbar-hide">
      
      {/* User Profile Snippet */}
      <div className="flex items-center gap-3 p-2 mb-4 hover:bg-muted rounded-xl cursor-pointer transition-colors">
        <Avatar className="h-9 w-9">
          <AvatarImage src={currentUser?.profile_photo || undefined} />
          <AvatarFallback>{currentUser?.name?.[0] || "U"}</AvatarFallback>
        </Avatar>
        <span className="font-semibold text-sm">{currentUser?.name || "Guest"}</span>
      </div>

      {/* Main Navigation */}
      <div className="space-y-1 mb-6">
        {menuItems.map((item) => (
          <Button
            key={item.id}
            variant="ghost"
            onClick={() => onFilterChange(item.id)}
            className={cn(
              "w-full justify-start gap-3 h-12 px-3 rounded-xl font-medium text-sm transition-all",
              currentFilter === item.id 
                ? "bg-primary/10 text-primary hover:bg-primary/15" 
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <item.icon className={cn("h-5 w-5", currentFilter === item.id ? "fill-current" : item.color)} />
            {item.label}
          </Button>
        ))}
        <Button variant="ghost" className="w-full justify-start gap-3 h-12 px-3 rounded-xl font-medium text-sm text-muted-foreground">
          <ChevronDown className="h-5 w-5 bg-muted rounded-full p-0.5" />
          See More
        </Button>
      </div>

      <div className="h-px bg-border my-2 mx-2" />

      {/* Shortcuts */}
      <div className="space-y-1 mt-4">
        <h3 className="px-3 text-xs font-bold text-muted-foreground/70 uppercase tracking-wider mb-2">Your Shortcuts</h3>
        {shortcuts.map((item, idx) => (
          <Button
            key={idx}
            variant="ghost"
            className="w-full justify-start gap-3 h-12 px-3 rounded-xl font-medium text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </Button>
        ))}
      </div>
      
      <div className="flex-1" />
      
      <div className="px-3 pb-4 text-[10px] text-muted-foreground/50">
        <p>Privacy  · Terms  · Advertising  · Ad Choices   · Cookies  ·  More · GarderieNova © 2026</p>
      </div>
    </div>
  );
}
