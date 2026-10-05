"use client";

import { usePushNotifications } from "@/hooks/use-push-notifications";
import { Button } from "@/components/ui/button";
import { Bell, X } from "lucide-react";
import { useState, useEffect } from "react";

export function PushNotificationPrompt() {
  const { permission, subscribeUser } = usePushNotifications();
  const [show, setShow] = useState(false);

  useEffect(() => {
    // Show prompt after 5 seconds if permission is still default
    const timer = setTimeout(() => {
      if (permission === 'default') {
        setShow(true);
      }
    }, 5000);
    return () => clearTimeout(timer);
  }, [permission]);

  if (!show || permission !== 'default') return null;

  return (
    <div className="fixed bottom-6 left-6 z-[200] max-w-sm bg-background border border-border shadow-2xl rounded-2xl p-4 animate-in slide-in-from-left-4 duration-500">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
          <Bell className="w-5 h-5 text-primary" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-bold">Enable Notifications</h3>
          <p className="text-xs text-muted-foreground mt-1">Get notified of new messages even when you're not on the site.</p>
          <div className="flex gap-2 mt-4">
            <Button size="sm" className="rounded-xl h-8 px-4 text-[10px] uppercase font-bold tracking-wider" onClick={() => {
              subscribeUser();
              setShow(false);
            }}>Allow</Button>
            <Button variant="ghost" size="sm" className="rounded-xl h-8 px-4 text-[10px] uppercase font-bold tracking-wider" onClick={() => setShow(false)}>Not now</Button>
          </div>
        </div>
        <button onClick={() => setShow(false)} className="text-muted-foreground hover:text-foreground">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
