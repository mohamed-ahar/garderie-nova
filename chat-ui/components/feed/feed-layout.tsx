"use client";

import { FeedNavbar } from "./feed-navbar";

interface FeedLayoutProps {
  children: React.ReactNode;
  currentUser: any;
  onSearch?: (query: string) => void;
}

export function FeedLayout({ children, currentUser, onSearch }: FeedLayoutProps) {
  return (
    <div className="min-h-screen bg-muted/10 font-sans">
      <FeedNavbar currentUser={currentUser} onSearch={onSearch} />
      
      <main className="flex justify-center">
        <div className="flex w-full max-w-[1440px] px-0 lg:px-4 relative justify-between">
          {children}
        </div>
      </main>
    </div>
  );
}
