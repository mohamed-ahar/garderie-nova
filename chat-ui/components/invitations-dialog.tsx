"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Check, X, Clock, Send, UserCheck, UserX } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { getCookie } from "@/lib/utils";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface Invitation {
  id: number;
  sender_name?: string;
  sender_id?: string;
  recipient_name?: string;
  recipient_id?: string;
  created_at: string;
}

export function InvitationsDialog({ isOpen, onClose, onActionSuccess }: { 
  isOpen: boolean; 
  onClose: () => void;
  onActionSuccess?: () => void;
}) {
  const [received, setReceived] = useState<Invitation[]>([]);
  const [sent, setSent] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchInvitations = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/chat/invitations/", {
        credentials: 'include'
      });
      const data = await res.json();
      setReceived(data.received);
      setSent(data.sent);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) fetchInvitations();
  }, [isOpen]);

  const handleAction = async (id: number, action: "accept" | "reject" | "revoke") => {
    const formData = new FormData();
    formData.append("action", action);
    try {
      await fetch(`http://localhost:8000/chat/invitations/${id}/manage/`, {
        method: "POST",
        body: formData,
        headers: { "X-CSRFToken": getCookie('csrftoken') || "" },
        credentials: 'include',
      });
      fetchInvitations();
      if (action === "accept") onActionSuccess?.();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[450px]">
        <DialogHeader>
          <DialogTitle>Chat Invitations</DialogTitle>
        </DialogHeader>
        
        <Tabs defaultValue="received" className="w-full mt-2">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="received" className="relative">
              Received
              {received.length > 0 && (
                <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
                  {received.length}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="sent">Sent</TabsTrigger>
          </TabsList>
          
          <TabsContent value="received" className="mt-4">
            <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto pr-2">
              {received.length === 0 ? (
                <div className="text-center py-8 text-sm text-muted-foreground">No pending invitations</div>
              ) : (
                received.map((invite) => (
                  <div key={invite.id} className="flex items-center justify-between p-3 rounded-lg border bg-card shadow-sm">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <Avatar className="h-9 w-9">
                        <AvatarFallback>{invite.sender_name?.[0]}</AvatarFallback>
                      </Avatar>
                      <div className="flex flex-col overflow-hidden">
                        <span className="text-sm font-medium truncate">{invite.sender_name}</span>
                        <span className="text-[10px] text-muted-foreground">
                          {new Date(invite.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button 
                        size="icon" 
                        variant="ghost" 
                        className="h-8 w-8 text-green-600 hover:text-green-700 hover:bg-green-50"
                        onClick={() => handleAction(invite.id, "accept")}
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                      <Button 
                        size="icon" 
                        variant="ghost" 
                        className="h-8 w-8 text-destructive hover:bg-destructive/10"
                        onClick={() => handleAction(invite.id, "reject")}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </TabsContent>
          
          <TabsContent value="sent" className="mt-4">
            <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto pr-2">
              {sent.length === 0 ? (
                <div className="text-center py-8 text-sm text-muted-foreground">You haven't sent any invitations</div>
              ) : (
                sent.map((invite) => (
                  <div key={invite.id} className="flex items-center justify-between p-3 rounded-lg border bg-card shadow-sm">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <Avatar className="h-9 w-9">
                        <AvatarFallback>{invite.recipient_name?.[0]}</AvatarFallback>
                      </Avatar>
                      <div className="flex flex-col overflow-hidden">
                        <span className="text-sm font-medium truncate">{invite.recipient_name}</span>
                        <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3 w-3" /> Pending
                        </span>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-muted-foreground hover:text-destructive"
                      onClick={() => handleAction(invite.id, "revoke")}
                    >
                      Revoke
                    </Button>
                  </div>
                ))
              )}
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
