// =============================================================================
// src/hooks/use-alerts.ts — Price alert system with browser notifications
// =============================================================================

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface PriceAlert {
  id: string;
  asset: string;
  condition: "above" | "below";
  targetPrice: number;
  createdAt: string;
  triggered: boolean;
  triggeredAt?: string;
}

const STORAGE_KEY = "jarvis-price-alerts";

function loadAlerts(): PriceAlert[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveAlerts(alerts: PriceAlert[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(alerts));
}

export function useAlerts() {
  const [alerts, setAlerts] = useState<PriceAlert[]>(loadAlerts);
  const [notificationPermission, setNotificationPermission] = useState<
    NotificationPermission | "unsupported"
  >("default");

  // Check notification permission on mount
  useEffect(() => {
    if (typeof Notification === "undefined") {
      setNotificationPermission("unsupported");
    } else {
      setNotificationPermission(Notification.permission);
    }
  }, []);

  const requestPermission = useCallback(async () => {
    if (typeof Notification === "undefined") return;
    const result = await Notification.requestPermission();
    setNotificationPermission(result);
  }, []);

  const addAlert = useCallback(
    (alert: Omit<PriceAlert, "id" | "createdAt" | "triggered">) => {
      const newAlert: PriceAlert = {
        ...alert,
        id: `alert-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        createdAt: new Date().toISOString(),
        triggered: false,
      };
      setAlerts((prev) => {
        const next = [newAlert, ...prev];
        saveAlerts(next);
        return next;
      });
      return newAlert;
    },
    []
  );

  const removeAlert = useCallback((id: string) => {
    setAlerts((prev) => {
      const next = prev.filter((a) => a.id !== id);
      saveAlerts(next);
      return next;
    });
  }, []);

  const clearTriggered = useCallback(() => {
    setAlerts((prev) => {
      const next = prev.filter((a) => !a.triggered);
      saveAlerts(next);
      return next;
    });
  }, []);

  // Check prices against active alerts
  const triggeredRef = useRef(new Set<string>());

  const checkPrices = useCallback(
    (prices: Record<string, number>) => {
      setAlerts((prev) => {
        let changed = false;
        const next = prev.map((alert) => {
          if (alert.triggered) return alert;
          if (triggeredRef.current.has(alert.id)) return alert;

          const price = prices[alert.asset];
          if (price === undefined) return alert;

          const shouldTrigger =
            (alert.condition === "above" && price >= alert.targetPrice) ||
            (alert.condition === "below" && price <= alert.targetPrice);

          if (shouldTrigger) {
            changed = true;
            triggeredRef.current.add(alert.id);

            // Browser notification
            if (
              typeof Notification !== "undefined" &&
              Notification.permission === "granted"
            ) {
              new Notification(`JARVIS Alert: ${alert.asset}`, {
                body: `${alert.asset} is now ${alert.condition === "above" ? "above" : "below"} $${alert.targetPrice.toLocaleString()} (Current: $${price.toLocaleString()})`,
                icon: "/icon-192.png",
                tag: alert.id,
              });
            }

            return {
              ...alert,
              triggered: true,
              triggeredAt: new Date().toISOString(),
            };
          }
          return alert;
        });

        if (changed) {
          saveAlerts(next);
        }
        return changed ? next : prev;
      });
    },
    []
  );

  const activeAlerts = alerts.filter((a) => !a.triggered);
  const triggeredAlerts = alerts.filter((a) => a.triggered);

  return {
    alerts,
    activeAlerts,
    triggeredAlerts,
    addAlert,
    removeAlert,
    clearTriggered,
    checkPrices,
    notificationPermission,
    requestPermission,
  };
}
