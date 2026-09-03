import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

// --- Chat Bubble Parent ---
const chatBubbleVariants = cva(
  "flex gap-3 max-w-[80%] items-end", 
  {
    variants: {
      variant: {
        received: "self-start",
        sent: "self-end flex-row-reverse",
      },
    },
    defaultVariants: {
      variant: "received",
    },
  }
);

interface ChatBubbleProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof chatBubbleVariants> {}

const ChatBubble = React.forwardRef<HTMLDivElement, ChatBubbleProps>(
  ({ className, variant, children, ...props }, ref) => (
    <div
      className={cn(chatBubbleVariants({ variant, className }))}
      ref={ref}
      {...props}
    >
      {children}
    </div>
  )
);
ChatBubble.displayName = "ChatBubble";

// --- Avatar Wrapper ---
interface ChatBubbleAvatarProps {
  src?: string;
  fallback?: string;
  className?: string;
}

const ChatBubbleAvatar = ({ src, fallback, className }: ChatBubbleAvatarProps) => (
  <Avatar className={cn("h-8 w-8", className)}>
    {src && <AvatarImage src={src} />}
    <AvatarFallback>{fallback}</AvatarFallback>
  </Avatar>
);

// --- Message Content ---
const chatBubbleMessageVariants = cva(
  "p-3 rounded-lg text-sm",
  {
    variants: {
      variant: {
        received: "bg-muted text-foreground rounded-bl-none",
        sent: "bg-primary text-primary-foreground rounded-br-none",
      },
    },
    defaultVariants: {
      variant: "received",
    },
  }
);

interface ChatBubbleMessageProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof chatBubbleMessageVariants> {
  isLoading?: boolean;
}

const ChatBubbleMessage = React.forwardRef<HTMLDivElement, ChatBubbleMessageProps>(
  ({ className, variant, isLoading, children, ...props }, ref) => (
    <div
      className={cn(chatBubbleMessageVariants({ variant, className }))}
      ref={ref}
      {...props}
    >
      {isLoading ? (
        <div className="flex items-center gap-1">
          <span className="animate-bounce">●</span>
          <span className="animate-bounce delay-100">●</span>
          <span className="animate-bounce delay-200">●</span>
        </div>
      ) : (
        children
      )}
    </div>
  )
);
ChatBubbleMessage.displayName = "ChatBubbleMessage";

export { ChatBubble, ChatBubbleAvatar, ChatBubbleMessage, chatBubbleVariants };