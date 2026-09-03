import { MoreVertical, Phone, Video } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

export function ChatHeader({ 
  isConnected, 
  selectedContact 
}: { 
  isConnected?: boolean;
  selectedContact?: { name: string; avatar: string } | null;
}) {
  return (
    <div className="flex h-16 items-center justify-between border-b px-4 bg-background">
      
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
        <Button variant="ghost" size="icon">
          <Phone className="h-5 w-5 text-muted-foreground" />
        </Button>
        <Button variant="ghost" size="icon">
          <Video className="h-5 w-5 text-muted-foreground" />
        </Button>
        <Button variant="ghost" size="icon">
          <MoreVertical className="h-5 w-5 text-muted-foreground" />
        </Button>
      </div>
    </div>
  );
}