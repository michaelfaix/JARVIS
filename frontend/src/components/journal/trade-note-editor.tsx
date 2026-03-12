// =============================================================================
// src/components/journal/trade-note-editor.tsx — Inline note/tag/rating editor
// =============================================================================

"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useTradeNotes, TAG_SUGGESTIONS } from "@/hooks/use-trade-notes";
import { Star, Save, X, Trash2 } from "lucide-react";

interface TradeNoteEditorProps {
  tradeId: string;
  onClose: () => void;
}

export function TradeNoteEditor({ tradeId, onClose }: TradeNoteEditorProps) {
  const { getNote, saveNote, deleteNote } = useTradeNotes();

  const [note, setNote] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [rating, setRating] = useState(0);
  const [hoveredStar, setHoveredStar] = useState(0);

  // Load existing note on mount
  useEffect(() => {
    const existing = getNote(tradeId);
    if (existing) {
      setNote(existing.note);
      setTags(existing.tags);
      setRating(existing.rating);
    }
  }, [tradeId, getNote]);

  function toggleTag(tag: string) {
    setTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }

  function handleSave() {
    saveNote(tradeId, note, tags, rating || 1);
    onClose();
  }

  function handleDelete() {
    deleteNote(tradeId);
    onClose();
  }

  return (
    <div className="bg-card/80 border border-border/50 rounded-lg p-3 space-y-3">
      {/* Note textarea */}
      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Add trade notes... What was your thesis? What went right/wrong?"
        rows={3}
        className="w-full bg-background/50 border border-border/50 rounded-md px-3 py-2 text-sm text-white placeholder:text-muted-foreground resize-y min-h-[72px] focus:outline-none focus:ring-1 focus:ring-blue-500/50"
      />

      {/* Tags */}
      <div>
        <div className="text-[10px] text-muted-foreground mb-1.5">Tags</div>
        <div className="flex flex-wrap gap-1.5">
          {TAG_SUGGESTIONS.map((tag) => {
            const selected = tags.includes(tag);
            return (
              <button
                key={tag}
                onClick={() => toggleTag(tag)}
                className={`px-2 py-0.5 rounded-full text-[11px] font-medium transition-colors ${
                  selected
                    ? "bg-blue-500/20 text-blue-400 border border-blue-500/40"
                    : "bg-muted/30 text-muted-foreground border border-border/30 hover:border-border/60"
                }`}
              >
                {tag}
              </button>
            );
          })}
        </div>
      </div>

      {/* Star rating */}
      <div>
        <div className="text-[10px] text-muted-foreground mb-1.5">
          Self-Assessment
        </div>
        <div className="flex items-center gap-0.5">
          {[1, 2, 3, 4, 5].map((star) => {
            const filled = star <= (hoveredStar || rating);
            return (
              <button
                key={star}
                onClick={() => setRating(star)}
                onMouseEnter={() => setHoveredStar(star)}
                onMouseLeave={() => setHoveredStar(0)}
                className="p-0.5 transition-colors"
              >
                <Star
                  className={`h-4 w-4 ${
                    filled
                      ? "fill-yellow-400 text-yellow-400"
                      : "text-muted-foreground/40"
                  }`}
                />
              </button>
            );
          })}
          {rating > 0 && (
            <span className="text-[10px] text-muted-foreground ml-1">
              {rating}/5
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1">
        <Button
          size="sm"
          className="h-7 text-xs gap-1"
          onClick={handleSave}
        >
          <Save className="h-3 w-3" />
          Save
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs gap-1"
          onClick={onClose}
        >
          <X className="h-3 w-3" />
          Cancel
        </Button>
        {getNote(tradeId) && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs gap-1 text-red-400 hover:text-red-300 ml-auto"
            onClick={handleDelete}
          >
            <Trash2 className="h-3 w-3" />
            Delete
          </Button>
        )}
      </div>
    </div>
  );
}
