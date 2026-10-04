"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Image as ImageIcon, Loader2, X, Users, User, Globe, Bell, Calendar, LayoutGrid, Video } from "lucide-react";
import { getCookie, cn } from "@/lib/utils";

interface Metadata {
  center_id: string;
  center_name: string;
  groups: { id: string; name: string }[];
  parents: { id: string; name: string }[];
}

interface CreatePostDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function CreatePostDialog({ isOpen, onClose, onSuccess }: CreatePostDialogProps) {
  const [content, setContent] = useState("");
  const [visibility, setVisibility] = useState<"all_parents" | "specific_groups" | "specific_parents">("all_parents");
  const [tags, setTags] = useState<string[]>(["general"]);
  const [selectedCenter, setSelectedCenter] = useState<string>("");
  const [selectedGroups, setSelectedGroups] = useState<string[]>([]);
  const [selectedParents, setSelectedParents] = useState<string[]>([]);
  const [mediaFiles, setMediaFiles] = useState<{file: File, preview: string, type: 'image' | 'video'}[]>([]);
  const [metadata, setMetadata] = useState<Metadata[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingMetadata, setIsFetchingMetadata] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsFetchingMetadata(true);
      fetch("http://localhost:8001/chat/feed/metadata/", { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
          setMetadata(data.metadata || []);
          if (data.metadata?.length > 0) {
            setSelectedCenter(data.metadata[0].center_id);
          }
          setIsFetchingMetadata(false);
        })
        .catch(err => {
          console.error("Failed to fetch metadata", err);
          setIsFetchingMetadata(false);
        });
    }
  }, [isOpen]);

  const toggleTag = (tag: string) => {
    setTags(prev => {
      if (tag === "general") {
        return ["general"];
      }
      let newTags = prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag];
      newTags = newTags.filter(t => t !== "general");
      if (newTags.length === 0) return ["general"];
      return newTags;
    });
  };

  const handleMediaChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      const newMedia = files.map(file => ({
        file,
        preview: URL.createObjectURL(file),
        type: file.type.startsWith('video/') ? 'video' as const : 'image' as const
      }));
      setMediaFiles(prev => [...prev, ...newMedia]);
      
      setTags(prev => {
        let newTags = [...prev];
        const hasVideo = newMedia.some(m => m.type === 'video');
        const hasImage = newMedia.some(m => m.type === 'image');
        if (hasVideo && !newTags.includes('videos')) newTags.push('videos');
        if (hasImage && !newTags.includes('photos')) newTags.push('photos');
        newTags = newTags.filter(t => t !== 'general');
        if (newTags.length === 0) return ['general'];
        return Array.from(new Set(newTags));
      });
    }
  };
  
  const removeMedia = (index: number) => {
    setMediaFiles(prev => {
      const newFiles = [...prev];
      URL.revokeObjectURL(newFiles[index].preview);
      newFiles.splice(index, 1);
      return newFiles;
    });
  }

  const handleSubmit = async () => {
    if (!content.trim() && mediaFiles.length === 0) return;
    setIsLoading(true);

    const formData = new FormData();
    formData.append("content", content);
    formData.append("visibility", visibility);
    formData.append("center_id", selectedCenter);
    
    tags.forEach(tag => formData.append("tags", tag));

    mediaFiles.forEach((media) => {
      formData.append("media", media.file);
    });
    
    selectedGroups.forEach(id => formData.append("target_groups", id));
    selectedParents.forEach(id => formData.append("target_parents", id));

    try {
      const res = await fetch("http://localhost:8001/chat/feed/create/", {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": getCookie('csrftoken') || "",
        },
        credentials: 'include',
      });

      if (res.ok) {
        setContent("");
        mediaFiles.forEach(m => URL.revokeObjectURL(m.preview));
        setMediaFiles([]);
        setSelectedGroups([]);
        setSelectedParents([]);
        setVisibility("all_parents");
        setTags(["general"]);
        onSuccess();
        onClose();
      }
    } catch (err) {
      console.error("Failed to create post", err);
    } finally {
      setIsLoading(false);
    }
  };

  const currentCenterMetadata = metadata.find(m => m.center_id === selectedCenter);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Center Announcement</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Center Selection */}
          {metadata.length > 1 && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Select Center</label>
              <select 
                className="w-full p-2 rounded-md border bg-background"
                value={selectedCenter}
                onChange={(e) => setSelectedCenter(e.target.value)}
              >
                {metadata.map(m => (
                  <option key={m.center_id} value={m.center_id}>{m.center_name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Post Type Tabs */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Post Tags</label>
            <div className="flex gap-2 p-1 bg-muted rounded-lg flex-wrap sm:flex-nowrap">
              <Button
                variant={tags.includes("general") ? "default" : "ghost"}
                size="sm"
                className="flex-1 gap-2 whitespace-nowrap"
                onClick={() => toggleTag("general")}
              >
                <LayoutGrid className="h-4 w-4" />
                General
              </Button>
              <Button
                variant={tags.includes("announcements") ? "default" : "ghost"}
                size="sm"
                className="flex-1 gap-2 whitespace-nowrap"
                onClick={() => toggleTag("announcements")}
              >
                <Bell className="h-4 w-4" />
                Announcement
              </Button>
              <Button
                variant={tags.includes("photos") ? "default" : "ghost"}
                size="sm"
                className="flex-1 gap-2 whitespace-nowrap"
                onClick={() => toggleTag("photos")}
              >
                <ImageIcon className="h-4 w-4" />
                Photo
              </Button>
              <Button
                variant={tags.includes("videos") ? "default" : "ghost"}
                size="sm"
                className="flex-1 gap-2 whitespace-nowrap"
                onClick={() => toggleTag("videos")}
              >
                <Video className="h-4 w-4" />
                Video
              </Button>
              <Button
                variant={tags.includes("events") ? "default" : "ghost"}
                size="sm"
                className="flex-1 gap-2 whitespace-nowrap"
                onClick={() => toggleTag("events")}
              >
                <Calendar className="h-4 w-4" />
                Event
              </Button>
            </div>
          </div>

          {/* Visibility Tabs */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Who can see this?</label>
            <div className="flex gap-2 p-1 bg-muted rounded-lg">
              <Button
                variant={visibility === "all_parents" ? "default" : "ghost"}
                size="sm"
                className="flex-1 gap-2"
                onClick={() => setVisibility("all_parents")}
              >
                <Globe className="h-4 w-4" />
                All Parents
              </Button>
              <Button
                variant={visibility === "specific_groups" ? "default" : "ghost"}
                size="sm"
                className="flex-1 gap-2"
                onClick={() => setVisibility("specific_groups")}
              >
                <Users className="h-4 w-4" />
                Groups
              </Button>
              <Button
                variant={visibility === "specific_parents" ? "default" : "ghost"}
                size="sm"
                className="flex-1 gap-2"
                onClick={() => setVisibility("specific_parents")}
              >
                <User className="h-4 w-4" />
                Specific
              </Button>
            </div>
          </div>

          {/* Target Group Selection */}
          {visibility === "specific_groups" && currentCenterMetadata && (
            <div className="space-y-2 animate-in fade-in slide-in-from-top-1">
              <label className="text-sm font-medium">Select Groups</label>
              <div className="flex flex-wrap gap-2">
                {currentCenterMetadata.groups.map(g => (
                  <button
                    key={g.id}
                    onClick={() => {
                      setSelectedGroups(prev => 
                        prev.includes(g.id) ? prev.filter(id => id !== g.id) : [...prev, g.id]
                      )
                    }}
                    className={cn(
                      "px-3 py-1.5 rounded-full text-xs font-medium border transition-colors",
                      selectedGroups.includes(g.id) 
                        ? "bg-primary text-primary-foreground border-primary" 
                        : "bg-background hover:bg-muted"
                    )}
                  >
                    {g.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Target Parent Selection */}
          {visibility === "specific_parents" && currentCenterMetadata && (
            <div className="space-y-2 animate-in fade-in slide-in-from-top-1">
              <label className="text-sm font-medium">Select Parents</label>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 border rounded-md">
                {currentCenterMetadata.parents.map(p => (
                  <button
                    key={p.id}
                    onClick={() => {
                      setSelectedParents(prev => 
                        prev.includes(p.id) ? prev.filter(id => id !== p.id) : [...prev, p.id]
                      )
                    }}
                    className={cn(
                      "px-3 py-1.5 rounded-full text-xs font-medium border transition-colors",
                      selectedParents.includes(p.id) 
                        ? "bg-primary text-primary-foreground border-primary" 
                        : "bg-background hover:bg-muted"
                    )}
                  >
                    {p.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          <Textarea 
            placeholder="Share something with the center..." 
            className="min-h-[150px] resize-none"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />

          {mediaFiles.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-4">
              {mediaFiles.map((media, index) => (
                <div key={index} className="relative rounded-lg overflow-hidden border bg-muted aspect-square">
                  {media.type === 'image' ? (
                    <img src={media.preview} alt={`Preview ${index}`} className="w-full h-full object-cover" />
                  ) : (
                    <video src={media.preview} className="w-full h-full object-cover" />
                  )}
                  <Button
                    variant="destructive"
                    size="icon"
                    className="absolute top-1 right-1 h-6 w-6 rounded-full opacity-80 hover:opacity-100 transition-opacity"
                    onClick={() => removeMedia(index)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center gap-2">
            <input 
              type="file" 
              id="post-media" 
              className="hidden" 
              multiple
              accept="image/*,video/*"
              onChange={handleMediaChange}
            />
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => document.getElementById('post-media')?.click()}
            >
              <ImageIcon className="h-4 w-4" />
              Add Photo / Video
            </Button>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button 
            disabled={isLoading || (!content.trim() && mediaFiles.length === 0)} 
            onClick={handleSubmit}
            className="px-8"
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Post Announcement
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
