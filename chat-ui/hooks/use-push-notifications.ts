"use client";

import { useEffect, useState } from 'react';

// Generated VAPID Public Key
const VAPID_PUBLIC_KEY = "BOxCGgI_7dafPEGpajQcQFGjfVstyBx92yBInyZWfFhUaDWVfOowYFy9WyfH30RwuFzRkr6deNdlJe9NdnihqSM";

export function usePushNotifications() {
  const [permission, setPermission] = useState<NotificationPermission>('default');

  useEffect(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      setPermission(Notification.permission);
    }
  }, []);

  const subscribeUser = async () => {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      console.warn("Push messaging is not supported");
      return;
    }

    try {
      // 1. Register the Service Worker
      const registration = await navigator.serviceWorker.register('/sw.js');
      
      // 2. Wait for it to be ready/activated
      await navigator.serviceWorker.ready;

      // 3. Attempt to subscribe
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      });

      // Send to backend
      const { p256dh, auth } = serializeSubscription(subscription);
      await fetch("http://localhost:8001/chat/subscribe-push/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie('csrftoken') || "",
        },
        body: JSON.stringify({
          endpoint: subscription.endpoint,
          p256dh,
          auth
        }),
        credentials: 'include',
      });

      setPermission('granted');
      return true;
    } catch (err) {
      console.error("Failed to subscribe", err);
      return false;
    }
  };

  return { permission, subscribeUser };
}

function urlBase64ToUint8Array(base64String: string) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function serializeSubscription(subscription: PushSubscription) {
  const json = subscription.toJSON();
  return {
    p256dh: json.keys?.p256dh || "",
    auth: json.keys?.auth || ""
  };
}

function getCookie(name: string) {
  let cookieValue = null;
  if (typeof document !== 'undefined' && document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
