"use client";

import { useState, useEffect } from "react";
import { Search, Bell, MessageCircle, Menu, LayoutGrid } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function FeedNavbar({ currentUser, onSearch }: { currentUser: any, onSearch?: (q: string) => void }) {
  const [searchValue, setSearchValue] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => {
      onSearch?.(searchValue);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchValue, onSearch]);

  return (
    <div className="h-14 sticky top-0 z-50 bg-background border-b shadow-sm w-full flex items-center justify-between px-4 lg:px-6">
      {/* Left: Logo */}
      <div className="flex items-center gap-2 lg:w-[280px]">
        <div className="w-9 h-9 rounded-full bg-primary flex items-center justify-center shrink-0">
          <LayoutGrid className="w-5 h-5 text-primary-foreground" />
        </div>
        <span className="font-bold text-xl tracking-tight hidden lg:block text-primary">GarderieNova</span>
      </div>

      {/* Center: Search */}
      <div className="hidden md:flex flex-1 max-w-[600px] px-4">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search posts or people..." 
            className="w-full bg-muted/50 border-none rounded-full pl-10 h-10 focus-visible:ring-1 focus-visible:ring-primary focus-visible:bg-background transition-all"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
        </div>
      </div>

      {/* Right: Actions & Profile */}
      <div className="flex items-center gap-2 lg:gap-3 lg:w-[280px] justify-end">
        <Button variant="ghost" size="icon" className="rounded-full bg-muted/50 h-10 w-10">
          <Menu className="w-5 h-5" />
        </Button>
        <Button variant="ghost" size="icon" className="rounded-full bg-muted/50 h-10 w-10">
          <MessageCircle className="w-5 h-5" />
        </Button>
        <Button variant="ghost" size="icon" className="rounded-full bg-muted/50 h-10 w-10 relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-background" />
        </Button>
        
        <Avatar className="h-10 w-10 border-2 border-background shadow-sm cursor-pointer ml-1">
          <AvatarImage src={currentUser?.profile_photo || undefined} />
          <AvatarFallback>{currentUser?.name?.[0] || "U"}</AvatarFallback>
        </Avatar>
      </div>
    </div>
  );
}
