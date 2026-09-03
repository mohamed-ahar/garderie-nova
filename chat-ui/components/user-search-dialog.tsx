"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, UserPlus, UserMinus, Clock, Check } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { getCookie } from "@/lib/utils";

interface SearchedUser {
  id: string;
  name: string;
  email: string;
  role: string;
  invitation_status: string;
}

export function UserSearchDialog({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [users, setUsers] = useState<SearchedUser[]>([]);
  const [loading, setLoading] = useState(false);

  const searchUsers = async (q: string) => {
    if (!q) {
      setUsers([]);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/chat/search-users/?q=${encodeURIComponent(q)}`, {
        credentials: 'include'
      });
      const data = await res.json();
      setUsers(data.users);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      searchUsers(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const sendInvite = async (userId: string) => {
    const formData = new FormData();
    formData.append("recipient_id", userId);
    try {
      await fetch("http://localhost:8000/chat/invitations/send/", {
        method: "POST",
        body: formData,
        headers: { "X-CSRFToken": getCookie('csrftoken') || "" },
        credentials: 'include',
      });
      searchUsers(query); // Refresh status
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Find People</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4 py-4">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by name or email..."
              className="pl-8"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto pr-2">
            {loading ? (
              <div className="text-center py-4 text-sm text-muted-foreground">Searching...</div>
            ) : users.length === 0 ? (
              <div className="text-center py-4 text-sm text-muted-foreground">{query ? "No users found" : "Type to search"}</div>
            ) : (
              users.map((user) => (
                <div key={user.id} className="flex items-center justify-between p-2 rounded-lg border bg-card text-card-foreground shadow-sm">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback>{user.name[0]}</AvatarFallback>
                    </Avatar>
                    <div className="flex flex-col overflow-hidden">
                      <span className="text-sm font-medium truncate">{user.name}</span>
                      <span className="text-[10px] text-muted-foreground uppercase">{user.role}</span>
                    </div>
                  </div>
                  
                  {user.invitation_status === "none" && (
                    <Button size="sm" variant="outline" className="h-8 gap-1" onClick={() => sendInvite(user.id)}>
                      <UserPlus className="h-3.5 w-3.5" />
                      Invite
                    </Button>
                  )}
                  {user.invitation_status === "sent_pending" && (
                    <div className="flex items-center gap-1 text-[10px] font-medium text-primary px-2 py-1 bg-primary/10 rounded-full">
                      <Clock className="h-3 w-3" />
                      Pending
                    </div>
                  )}
                  {user.invitation_status.includes("accepted") && (
                    <div className="flex items-center gap-1 text-[10px] font-medium text-green-600 px-2 py-1 bg-green-50 rounded-full">
                      <Check className="h-3 w-3" />
                      Connected
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
