"use client";

import { useState, useEffect, useRef } from "react";
import { X, Minus, Send, Phone, Video, MoreVertical, Loader2, Image as ImageIcon, Smile } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChat, Message } from "@/hooks/use-chat";
import { cn } from "@/lib/utils";

interface MiniChatBoxProps {
  contact: {
    id: string;
    name: string;
    profile_photo?: string | null;
    is_online?: boolean;
  };
  currentUserId: string;
  currentUser: any;
  onClose: () => void;
}

export function MiniChatBox({ contact, currentUserId, currentUser, onClose }: MiniChatBoxProps) {
  const [isMinimized, setIsMinimized] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { messages, sendMessage, isConnected, isLoadingHistory } = useChat(
    contact.id,
    currentUserId,
    undefined,
    undefined,
    currentUser
  );

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current && !isMinimized) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth"
      });
    }
  }, [messages, isMinimized]);

  // Adjust textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "inherit";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [inputValue]);

  const handleSend = () => {
    if (inputValue.trim()) {
      sendMessage(inputValue);
      setInputValue("");
    }
  };

  if (isMinimized) {
    return (
      <div 
        className="w-48 bg-background border border-border shadow-lg rounded-t-lg cursor-pointer hover:bg-accent transition-colors"
        onClick={() => setIsMinimized(false)}
      >
        <div className="flex items-center justify-between p-2">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="relative shrink-0">
              <Avatar className="h-6 w-6">
                <AvatarImage src={contact.profile_photo || undefined} />
                <AvatarFallback>{contact.name[0]}</AvatarFallback>
              </Avatar>
              {contact.is_online && (
                <span className="absolute bottom-0 right-0 w-2 h-2 bg-green-500 border border-background rounded-full animate-pulse" />
              )}
            </div>
            <span className="text-xs font-bold truncate">{contact.name}</span>
          </div>
          <button onClick={(e) => { e.stopPropagation(); onClose(); }} className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 h-[450px] bg-background border border-border shadow-2xl rounded-t-xl flex flex-col animate-in slide-in-from-bottom-2 duration-300">
      {/* Header */}
      <div className="p-2 border-b flex items-center justify-between bg-background rounded-t-xl shadow-sm">
        <div className="flex items-center gap-2 group cursor-pointer">
          <div className="relative shrink-0">
            <Avatar className="h-8 w-8 ring-2 ring-background ring-offset-1">
              <AvatarImage src={contact.profile_photo || undefined} />
              <AvatarFallback>{contact.name[0]}</AvatarFallback>
            </Avatar>
            {contact.is_online && (
              <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-500 border-2 border-background rounded-full animate-pulse" />
            )}
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-xs font-bold truncate group-hover:underline">{contact.name}</span>
            <div className="flex items-center gap-1">
               <span className="text-[9px] text-muted-foreground uppercase font-bold tracking-tight">{contact.is_online ? "Active now" : "Offline"}</span>
               {isConnected && <div className="w-1 h-1 rounded-full bg-primary" />}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-0.5">
          <Button variant="ghost" size="icon" className="h-8 w-8 text-primary rounded-full hover:bg-primary/10"><Phone className="h-4 w-4" /></Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-primary rounded-full hover:bg-primary/10"><Video className="h-4 w-4" /></Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground rounded-full hover:bg-muted" onClick={() => setIsMinimized(true)}><Minus className="h-4 w-4" /></Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground rounded-full hover:bg-destructive/10 hover:text-destructive" onClick={onClose}><X className="h-4 w-4" /></Button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-hidden relative bg-muted/5">
        <ScrollArea className="h-full p-3" viewportRef={scrollRef}>
          <div className="space-y-3">
            {isLoadingHistory && (
              <div className="flex justify-center py-4">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            )}
            
            {messages.map((msg, idx) => (
              <div 
                key={msg.id || idx} 
                className={cn(
                  "flex flex-col max-w-[85%]",
                  msg.role === "user" ? "ml-auto items-end" : "mr-auto items-start"
                )}
              >
                <div 
                  className={cn(
                    "px-3 py-1.5 rounded-2xl text-xs shadow-sm leading-relaxed",
                    msg.role === "user" 
                      ? "bg-primary text-primary-foreground rounded-tr-none" 
                      : "bg-background text-foreground rounded-tl-none border border-border/50"
                  )}
                >
                  {msg.content}
                </div>
                {idx === messages.length - 1 && msg.role === "user" && (
                  <span className="text-[9px] text-muted-foreground mt-0.5 font-medium px-1">
                    {msg.is_read ? "Seen" : msg.is_delivered ? "Delivered" : "Sent"}
                  </span>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Footer */}
      <div className="p-2 border-t bg-background">
        <div className="flex items-end gap-1 px-1 py-1">
          <div className="flex items-center gap-0.5 pb-1">
            <Button variant="ghost" size="icon" className="h-8 w-8 text-primary shrink-0 rounded-full hover:bg-primary/10"><ImageIcon className="h-4 w-4" /></Button>
            <Button variant="ghost" size="icon" className="h-8 w-8 text-primary shrink-0 rounded-full hover:bg-primary/10"><Smile className="h-4 w-4" /></Button>
          </div>
          
          <div className="flex-1 relative">
            <Textarea 
              ref={textareaRef}
              placeholder="Aa" 
              className="min-h-[36px] max-h-[120px] bg-muted/50 border-none rounded-2xl text-xs focus-visible:ring-1 focus-visible:ring-primary resize-none py-2 px-3 transition-all overflow-y-auto"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
          </div>
          
          <div className="pb-1">
            <Button 
              variant="ghost" 
              size="icon" 
              className={cn(
                "h-8 w-8 shrink-0 transition-all rounded-full hover:bg-primary/10", 
                inputValue.trim() ? "text-primary scale-110" : "text-muted-foreground"
              )}
              onClick={handleSend}
              disabled={!inputValue.trim()}
            >
              <Send className="h-4 w-4 fill-current" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
