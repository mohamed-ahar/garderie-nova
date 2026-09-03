"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { UserX, ShieldCheck } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { getCookie } from "@/lib/utils";

interface BlockedUser {
  id: string;
  name: string;
  email: string;
  role: string;
}

export function BlockedUsersDialog({ isOpen, onClose, onUnblockSuccess }: { 
  isOpen: boolean; 
  onClose: () => void;
  onUnblockSuccess?: () => void;
}) {
  const [blockedUsers, setBlockedUsers] = useState<BlockedUser[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchBlockedUsers = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/chat/blocked-users/", {
        credentials: 'include'
      });
      const data = await res.json();
      setBlockedUsers(data.blocked_users);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) fetchBlockedUsers();
  }, [isOpen]);

  const handleUnblock = async (userId: string) => {
    try {
      await fetch(`http://localhost:8000/chat/users/${userId}/unblock/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie('csrftoken') || "" },
        credentials: 'include',
      });
      fetchBlockedUsers();
      onUnblockSuccess?.();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserX className="h-5 w-5 text-destructive" />
            Blocked Users
          </DialogTitle>
        </DialogHeader>
        
        <div className="flex flex-col gap-2 mt-4 max-h-[300px] overflow-y-auto pr-2">
          {loading ? (
            <div className="text-center py-8 text-sm text-muted-foreground">Loading...</div>
          ) : blockedUsers.length === 0 ? (
            <div className="text-center py-12 flex flex-col items-center gap-3">
              <ShieldCheck className="h-12 w-12 text-muted-foreground/20" />
              <p className="text-sm text-muted-foreground">No users blocked</p>
            </div>
          ) : (
            blockedUsers.map((user) => (
              <div key={user.id} className="flex items-center justify-between p-3 rounded-lg border bg-card shadow-sm">
                <div className="flex items-center gap-3 overflow-hidden">
                  <Avatar className="h-9 w-9">
                    <AvatarFallback>{user.name[0]}</AvatarFallback>
                  </Avatar>
                  <div className="flex flex-col overflow-hidden">
                    <span className="text-sm font-medium truncate">{user.name}</span>
                    <span className="text-[10px] text-muted-foreground uppercase">{user.role}</span>
                  </div>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="h-8 text-xs font-semibold hover:bg-primary hover:text-primary-foreground transition-all"
                  onClick={() => handleUnblock(user.id)}
                >
                  Unblock
                </Button>
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
