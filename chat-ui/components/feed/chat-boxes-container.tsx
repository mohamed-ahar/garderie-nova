"use client";

import { MiniChatBox } from "./mini-chat-box";

interface ChatBoxesContainerProps {
  openChats: any[];
  currentUserId: string;
  currentUser: any;
  onCloseChat: (contactId: string) => void;
}

export function ChatBoxesContainer({ openChats, currentUserId, currentUser, onCloseChat }: ChatBoxesContainerProps) {
  return (
    <div className="fixed bottom-0 right-4 z-[100] flex flex-row-reverse items-end gap-4 pointer-events-none">
      {openChats.map((contact) => (
        <div key={contact.id} className="pointer-events-auto">
          <MiniChatBox 
            contact={contact} 
            currentUserId={currentUserId}
            currentUser={currentUser}
            onClose={() => onCloseChat(contact.id)}
          />
        </div>
      ))}
    </div>
  );
}
