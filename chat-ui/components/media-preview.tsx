"use client";

import { X, ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useCallback, useRef } from "react";
import { Button } from "./ui/button";
import { cn } from "@/lib/utils";

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
  const overlayRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

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

  // Handle keyboard events: Escape to close, Arrows for navigation, and Focus Trapping
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowLeft") handlePrevious();
      if (e.key === "ArrowRight") handleNext();
      
      // Simple Focus Trapping
      if (e.key === "Tab") {
        const focusableElements = overlayRef.current?.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements && focusableElements.length > 0) {
          const firstElement = focusableElements[0] as HTMLElement;
          const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

          if (e.shiftKey) {
            if (document.activeElement === firstElement) {
              lastElement.focus();
              e.preventDefault();
            }
          } else {
            if (document.activeElement === lastElement) {
              firstElement.focus();
              e.preventDefault();
            }
          }
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    // Focus close button on open
    setTimeout(() => closeButtonRef.current?.focus(), 50);
    
    // Prevent body scroll when open
    document.body.style.overflow = 'hidden';

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose, handlePrevious, handleNext]);

  if (!isOpen || !currentMedia) return null;

  return (
    <div 
      ref={overlayRef}
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-black/85 backdrop-blur-md transition-all animate-in fade-in duration-200"
      onClick={onClose}
      onContextMenu={(e) => e.preventDefault()}
    >
      {/* Header / Controls */}
      <div className="absolute top-0 left-0 right-0 p-6 flex justify-between items-center z-50 pointer-events-none">
        <div className="text-white/70 text-xs font-bold uppercase tracking-widest bg-black/20 px-3 py-1.5 rounded-full backdrop-blur-sm">
          {currentIndex + 1} <span className="mx-1 opacity-50">/</span> {mediaItems.length}
        </div>
        <Button
          ref={closeButtonRef}
          variant="ghost"
          size="icon"
          className="text-white hover:bg-white/20 rounded-full h-12 w-12 pointer-events-auto bg-black/20 backdrop-blur-sm shadow-xl transition-transform hover:scale-110 active:scale-95"
          onClick={(e) => {
            e.stopPropagation();
            onClose();
          }}
          title="Close (Esc)"
        >
          <X className="h-6 w-6" strokeWidth={3} />
        </Button>
      </div>

      {/* Content Area */}
      <div className="relative w-full h-full flex items-center justify-center p-4 md:p-8">
        
        {/* Transparent Navigation Overlays (to capture clicks while pointer-events: none is on img) */}
        <div className="absolute inset-0 flex z-10">
          <div 
            className="flex-1 cursor-pointer group flex items-center justify-start p-4"
            onClick={(e) => {
              if (currentIndex > 0) {
                e.stopPropagation();
                handlePrevious();
              }
            }}
          >
            {currentIndex > 0 && (
              <div className="p-4 rounded-full bg-black/20 text-white/50 group-hover:bg-black/40 group-hover:text-white transition-all transform group-hover:scale-110">
                <ChevronLeft className="h-10 w-10" />
              </div>
            )}
          </div>
          <div 
            className="flex-1 cursor-pointer group flex items-center justify-end p-4"
            onClick={(e) => {
              if (currentIndex < mediaItems.length - 1) {
                e.stopPropagation();
                handleNext();
              }
            }}
          >
            {currentIndex < mediaItems.length - 1 && (
              <div className="p-4 rounded-full bg-black/20 text-white/50 group-hover:bg-black/40 group-hover:text-white transition-all transform group-hover:scale-110">
                <ChevronRight className="h-10 w-10" />
              </div>
            )}
          </div>
        </div>

        {/* Media Display */}
        <div 
          className="relative max-w-[90vw] max-h-[90vh] flex items-center justify-center animate-in zoom-in-95 duration-300"
          onClick={(e) => e.stopPropagation()}
        >
          {currentMedia.type === "image" ? (
            <img
              src={currentMedia.url}
              alt="Preview"
              className="max-w-full max-h-[90vh] object-contain shadow-2xl select-none pointer-events-none"
              onContextMenu={(e) => e.preventDefault()}
            />
          ) : (
            <video
              src={currentMedia.url}
              controls
              autoPlay
              className="max-w-full max-h-[90vh] shadow-2xl rounded-lg"
              onClick={(e) => e.stopPropagation()}
              onContextMenu={(e) => e.preventDefault()}
            />
          )}
        </div>
      </div>

      {/* Mobile Swipe Dismissal Instruction (Optional visual hint) */}
      <div className="absolute bottom-8 left-0 right-0 flex justify-center pointer-events-none">
        <div className="h-1 w-12 rounded-full bg-white/20 animate-pulse" />
      </div>
    </div>
  );
}
