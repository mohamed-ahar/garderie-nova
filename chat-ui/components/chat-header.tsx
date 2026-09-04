import { MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

export function ChatHeader({ 
  isConnected, 
  selectedContact
}: { 
  isConnected?: boolean;
  selectedContact?: { 
    id: string; 
    name: string; 
    avatar: string; 
    profile_photo?: string | null;
    is_online?: boolean; 
    last_seen?: string;
  } | null;
}) {
  const formatLastSeen = (dateStr?: string) => {
    if (!dateStr) return "Offline";
    try {
      const date = new Date(dateStr);
      return `Last seen ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } catch (e) {
      return "Offline";
    }
  };

  return (
    <div className="flex h-full w-full items-center justify-between bg-background">
      
      {/* Active Chat Info */}
      <div className="flex items-center gap-3">
        <Avatar>
          <AvatarImage src={selectedContact?.profile_photo || undefined} className="object-cover" />
          <AvatarFallback>{selectedContact?.avatar || "???"}</AvatarFallback>
        </Avatar>
        <div>
          <h3 className="font-semibold text-sm">{selectedContact?.name || "Select a chat"}</h3>
          <p className={cn(
            "text-xs flex items-center gap-1",
            selectedContact?.is_online ? "text-green-500" : "text-muted-foreground"
          )}>
            <span className={cn(
              "block h-2 w-2 rounded-full",
              selectedContact?.is_online ? "bg-green-500" : "bg-gray-400"
            )} />
            {selectedContact?.is_online ? "Online" : formatLastSeen(selectedContact?.last_seen)}
          </p>
        </div>
      </div>

      {/* Header Actions */}
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon">
          <MoreVertical className="h-5 w-5 text-muted-foreground" />
        </Button>
      </div>
    </div>
  );
}