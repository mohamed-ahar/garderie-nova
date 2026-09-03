"use client";

import { X, ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useCallback } from "react";
import { Button } from "./ui/button";

interface MediaItem {
  url: string;
  type: "image" | "video";
  id: string | number;
}

interface MediaPreviewProps {
  isOpen: boolean;
  onClose: () => void;
  mediaItems: MediaItem[];
  currentIndex: number;
  onIndexChange: (index: number) => void;
}

export function MediaPreview({
  isOpen,
  onClose,
  mediaItems,
  currentIndex,
  onIndexChange,
}: MediaPreviewProps) {
  const currentMedia = mediaItems[currentIndex];

  const handlePrevious = useCallback(() => {
    if (currentIndex > 0) {
      onIndexChange(currentIndex - 1);
    }
  }, [currentIndex, onIndexChange]);

  const handleNext = useCallback(() => {
    if (currentIndex < mediaItems.length - 1) {
      onIndexChange(currentIndex + 1);
    }
  }, [currentIndex, mediaItems.length, onIndexChange]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowLeft") handlePrevious();
      if (e.key === "ArrowRight") handleNext();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, handlePrevious, handleNext]);

  if (!isOpen || !currentMedia) return null;

  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-black/90 backdrop-blur-md transition-all animate-in fade-in duration-200">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 p-4 flex justify-between items-center bg-gradient-to-b from-black/50 to-transparent z-10">
        <div className="text-white text-sm font-medium">
          {currentIndex + 1} / {mediaItems.length}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-white/20 rounded-full"
          onClick={onClose}
        >
          <X className="h-6 w-6" />
        </Button>
      </div>

      {/* Content */}
      <div className="relative w-full h-full flex items-center justify-center p-4 md:p-12">
        {/* Navigation Buttons */}
        {currentIndex > 0 && (
          <button
            className="absolute left-4 z-20 p-2 rounded-full bg-black/40 text-white hover:bg-black/60 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              handlePrevious();
            }}
          >
            <ChevronLeft className="h-8 w-8" />
          </button>
        )}

        {currentIndex < mediaItems.length - 1 && (
          <button
            className="absolute right-4 z-20 p-2 rounded-full bg-black/40 text-white hover:bg-black/60 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              handleNext();
            }}
          >
            <ChevronRight className="h-8 w-8" />
          </button>
        )}

        {/* Media Display */}
        <div className="max-w-full max-h-full flex items-center justify-center animate-in zoom-in-95 duration-300">
          {currentMedia.type === "image" ? (
            <img
              src={currentMedia.url}
              alt="Preview"
              className="max-w-full max-h-[85vh] object-contain shadow-2xl"
            />
          ) : (
            <video
              src={currentMedia.url}
              controls
              autoPlay
              className="max-w-full max-h-[85vh] shadow-2xl"
            />
          )}
        </div>
      </div>

      {/* Footer / Caption (Optional) */}
      <div className="absolute bottom-0 left-0 right-0 p-6 text-center bg-gradient-to-t from-black/50 to-transparent">
        {/* You could add content/caption here if needed */}
      </div>
    </div>
  );
}
