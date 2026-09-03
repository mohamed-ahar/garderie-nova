import { MoreVertical, Ban } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn, getCookie } from "@/lib/utils";

export function ChatHeader({ 
  isConnected, 
  selectedContact,
  onBlockUpdate
}: { 
  isConnected?: boolean;
  selectedContact?: { id: string; name: string; avatar: string; is_blocked?: boolean } | null;
  onBlockUpdate?: () => void;
}) {
  const handleBlock = async () => {
    if (!selectedContact) return;
    const url = `http://localhost:8000/chat/users/${selectedContact.id}/${selectedContact.is_blocked ? 'unblock' : 'block'}/`;
    try {
      await fetch(url, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie('csrftoken') || "" },
        credentials: 'include',
      });
      onBlockUpdate?.();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex h-full w-full items-center justify-between bg-background">
      
      {/* Active Chat Info */}
      <div className="flex items-center gap-3">
        <Avatar>
          <AvatarFallback>{selectedContact?.avatar || "???"}</AvatarFallback>
        </Avatar>
        <div>
          <h3 className="font-semibold text-sm">{selectedContact?.name || "Select a chat"}</h3>
          <p className={cn(
            "text-xs flex items-center gap-1",
            isConnected ? "text-green-500" : "text-red-500"
          )}>
            <span className={cn(
              "block h-2 w-2 rounded-full",
              isConnected ? "bg-green-500" : "bg-red-500"
            )} />
            {isConnected ? "Online" : "Offline"}
          </p>
        </div>
      </div>

      {/* Header Actions */}
      <div className="flex items-center gap-1">
        <Button 
          variant="ghost" 
          size="sm" 
          className={cn("gap-2", selectedContact?.is_blocked ? "text-primary" : "text-destructive")}
          onClick={handleBlock}
        >
          <Ban className="h-4 w-4" />
          {selectedContact?.is_blocked ? "Unblock" : "Block"}
        </Button>
        <Button variant="ghost" size="icon">
          <MoreVertical className="h-5 w-5 text-muted-foreground" />
        </Button>
      </div>
    </div>
  );
}