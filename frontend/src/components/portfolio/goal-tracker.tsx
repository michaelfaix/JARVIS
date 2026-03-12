// =============================================================================
// src/components/portfolio/goal-tracker.tsx — Portfolio Goal Tracker
// =============================================================================

"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Target,
  Plus,
  X,
  Calendar,
  TrendingUp,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PortfolioGoal {
  id: string;
  title: string;
  targetValue: number;
  deadline: string; // ISO date
  createdAt: string;
}

interface GoalTrackerProps {
  currentValue: number;
  startingCapital: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STORAGE_KEY = "jarvis-portfolio-goals";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function generateId(): string {
  return `goal-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function daysRemaining(deadline: string): number {
  const now = new Date();
  const end = new Date(deadline);
  const diff = end.getTime() - now.getTime();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function requiredDailyReturn(
  currentValue: number,
  targetValue: number,
  deadline: string
): number | null {
  const days = daysRemaining(deadline);
  if (days <= 0 || currentValue <= 0) return null;
  // compound daily return: (target / current)^(1/days) - 1
  const ratio = targetValue / currentValue;
  if (ratio <= 1) return 0;
  return (Math.pow(ratio, 1 / days) - 1) * 100;
}

type GoalStatus = "Completed" | "Expired" | "On Track" | "Behind";

function getGoalStatus(
  currentValue: number,
  targetValue: number,
  deadline: string,
  createdAt: string
): GoalStatus {
  const progress = currentValue / targetValue;

  if (progress >= 1) return "Completed";

  const days = daysRemaining(deadline);
  if (days <= 0) return "Expired";

  // Calculate expected progress based on linear interpolation from creation
  const created = new Date(createdAt).getTime();
  const end = new Date(deadline).getTime();
  const now = Date.now();
  const totalDuration = end - created;
  const elapsed = now - created;
  const expectedProgress = totalDuration > 0 ? elapsed / totalDuration : 1;

  return progress >= expectedProgress * 0.8 ? "On Track" : "Behind";
}

function statusColor(status: GoalStatus): string {
  switch (status) {
    case "Completed":
      return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    case "On Track":
      return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
    case "Behind":
      return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    case "Expired":
      return "bg-red-500/20 text-red-400 border-red-500/30";
  }
}

function progressBarColor(status: GoalStatus): string {
  switch (status) {
    case "Completed":
      return "bg-blue-500";
    case "On Track":
      return "bg-emerald-500";
    case "Behind":
      return "bg-yellow-500";
    case "Expired":
      return "bg-red-500";
  }
}

function fmtUsd(n: number): string {
  return `$${n.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function createDefaultGoals(startingCapital: number): PortfolioGoal[] {
  const now = new Date();
  return [
    {
      id: generateId(),
      title: "First Profit",
      targetValue: startingCapital * 1.01,
      deadline: new Date(
        now.getTime() + 7 * 24 * 60 * 60 * 1000
      ).toISOString(),
      createdAt: now.toISOString(),
    },
    {
      id: generateId(),
      title: "10% Return",
      targetValue: startingCapital * 1.1,
      deadline: new Date(
        now.getTime() + 30 * 24 * 60 * 60 * 1000
      ).toISOString(),
      createdAt: now.toISOString(),
    },
    {
      id: generateId(),
      title: "Double Portfolio",
      targetValue: startingCapital * 2,
      deadline: new Date(
        now.getTime() + 365 * 24 * 60 * 60 * 1000
      ).toISOString(),
      createdAt: now.toISOString(),
    },
  ];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function GoalTracker({
  currentValue,
  startingCapital,
}: GoalTrackerProps) {
  const [goals, setGoals] = useState<PortfolioGoal[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [targetValue, setTargetValue] = useState("");
  const [deadline, setDeadline] = useState("");
  const [error, setError] = useState("");

  // Load goals from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as PortfolioGoal[];
        if (Array.isArray(parsed) && parsed.length > 0) {
          setGoals(parsed);
          return;
        }
      }
    } catch {
      // Ignore parse errors
    }
    // No valid stored goals — create defaults
    const defaults = createDefaultGoals(startingCapital);
    setGoals(defaults);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(defaults));
  }, [startingCapital]);

  // Persist goals on change
  const persist = useCallback((updated: PortfolioGoal[]) => {
    setGoals(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  }, []);

  // Add a new goal
  const handleAddGoal = () => {
    setError("");
    const target = parseFloat(targetValue);

    if (!title.trim()) {
      setError("Title is required.");
      return;
    }
    if (isNaN(target) || target <= currentValue) {
      setError(`Target must be greater than current value (${fmtUsd(currentValue)}).`);
      return;
    }
    if (!deadline) {
      setError("Deadline is required.");
      return;
    }
    const deadlineDate = new Date(deadline);
    if (deadlineDate.getTime() <= Date.now()) {
      setError("Deadline must be in the future.");
      return;
    }

    const newGoal: PortfolioGoal = {
      id: generateId(),
      title: title.trim(),
      targetValue: target,
      deadline: deadlineDate.toISOString(),
      createdAt: new Date().toISOString(),
    };

    persist([...goals, newGoal]);
    setTitle("");
    setTargetValue("");
    setDeadline("");
    setShowForm(false);
  };

  // Remove a goal
  const handleRemoveGoal = (id: string) => {
    persist(goals.filter((g) => g.id !== id));
  };

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base font-semibold">
            <Target className="h-4 w-4 text-primary" />
            Portfolio Goals
          </CardTitle>
          <button
            onClick={() => setShowForm(!showForm)}
            className={cn(
              "flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
              showForm
                ? "bg-muted text-muted-foreground"
                : "bg-primary/10 text-primary hover:bg-primary/20"
            )}
          >
            {showForm ? (
              <X className="h-3 w-3" />
            ) : (
              <Plus className="h-3 w-3" />
            )}
            {showForm ? "Cancel" : "Add Goal"}
          </button>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* ---- Add Goal Form ---- */}
        {showForm && (
          <div className="rounded-lg border border-border/50 bg-muted/30 p-3 space-y-2.5">
            <input
              type="text"
              placeholder="e.g., Double my portfolio"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <div className="grid grid-cols-2 gap-2">
              <input
                type="number"
                placeholder="$20,000"
                value={targetValue}
                onChange={(e) => setTargetValue(e.target.value)}
                className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                min={0}
                step="any"
              />
              <input
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            {error && (
              <p className="text-xs text-red-400">{error}</p>
            )}
            <button
              onClick={handleAddGoal}
              className="w-full rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Add Goal
            </button>
          </div>
        )}

        {/* ---- Goal Cards Grid ---- */}
        {goals.length === 0 && !showForm ? (
          <p className="text-xs text-muted-foreground text-center py-4">
            No goals yet. Click &quot;Add Goal&quot; to get started.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">
            {goals.map((goal) => {
              const progress = Math.min(
                (currentValue / goal.targetValue) * 100,
                100
              );
              const days = daysRemaining(goal.deadline);
              const dailyReturn = requiredDailyReturn(
                currentValue,
                goal.targetValue,
                goal.deadline
              );
              const status = getGoalStatus(
                currentValue,
                goal.targetValue,
                goal.deadline,
                goal.createdAt
              );

              return (
                <div
                  key={goal.id}
                  className="rounded-lg border border-border/50 bg-muted/20 p-3 space-y-2"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">
                        {goal.title}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Target: {fmtUsd(goal.targetValue)}
                      </p>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <Badge
                        className={cn(
                          "text-[10px] px-1.5 py-0",
                          statusColor(status)
                        )}
                      >
                        {status === "Completed" && (
                          <CheckCircle2 className="h-2.5 w-2.5 mr-0.5" />
                        )}
                        {status}
                      </Badge>
                      <button
                        onClick={() => handleRemoveGoal(goal.id)}
                        className="rounded p-0.5 text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        aria-label={`Remove goal: ${goal.title}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                      <span>{progress.toFixed(1)}%</span>
                      <span>{fmtUsd(currentValue)} / {fmtUsd(goal.targetValue)}</span>
                    </div>
                    <Progress
                      value={progress}
                      className="h-1.5"
                      indicatorClassName={progressBarColor(status)}
                    />
                  </div>

                  {/* Footer Stats */}
                  <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-0.5">
                      <Calendar className="h-2.5 w-2.5" />
                      {days > 0
                        ? `${days}d remaining`
                        : days === 0
                          ? "Due today"
                          : `${Math.abs(days)}d overdue`}
                    </span>
                    {dailyReturn !== null && dailyReturn > 0 && status !== "Completed" && (
                      <span className="flex items-center gap-0.5">
                        <TrendingUp className="h-2.5 w-2.5" />
                        {dailyReturn < 0.01
                          ? "<0.01"
                          : dailyReturn.toFixed(2)}
                        %/day needed
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
