// =============================================================================
// src/hooks/use-notifications.ts — Centralized notification store (Context)
// =============================================================================

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from "react";
import React from "react";

export type NotificationType = "signal" | "alert" | "achievement" | "trade" | "system";

export interface AppNotification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

const STORAGE_KEY = "jarvis-notifications";
const MAX_NOTIFICATIONS = 50;

function load(): AppNotification[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function save(notifications: AppNotification[]) {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(notifications.slice(0, MAX_NOTIFICATIONS))
  );
}

interface NotificationContextValue {
  notifications: AppNotification[];
  push: (type: NotificationType, title: string, message: string) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  clearAll: () => void;
  unreadCount: number;
  lastPushedAt: number;
}

const NotificationContext = createContext<NotificationContextValue | null>(null);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<AppNotification[]>(load);
  const [lastPushedAt, setLastPushedAt] = useState(0);

  const push = useCallback(
    (type: NotificationType, title: string, message: string) => {
      const n: AppNotification = {
        id: `notif-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        type,
        title,
        message,
        timestamp: new Date().toISOString(),
        read: false,
      };
      setNotifications((prev) => {
        const next = [n, ...prev].slice(0, MAX_NOTIFICATIONS);
        save(next);
        return next;
      });
      setLastPushedAt(Date.now());
    },
    []
  );

  const markRead = useCallback((id: string) => {
    setNotifications((prev) => {
      const next = prev.map((n) =>
        n.id === id ? { ...n, read: true } : n
      );
      save(next);
      return next;
    });
  }, []);

  const markAllRead = useCallback(() => {
    setNotifications((prev) => {
      const next = prev.map((n) => ({ ...n, read: true }));
      save(next);
      return next;
    });
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
    save([]);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return React.createElement(
    NotificationContext.Provider,
    { value: { notifications, push, markRead, markAllRead, clearAll, unreadCount, lastPushedAt } },
    children
  );
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) {
    throw new Error("useNotifications must be used within a NotificationProvider");
  }
  return ctx;
}
