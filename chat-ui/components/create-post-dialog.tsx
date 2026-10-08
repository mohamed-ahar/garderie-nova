"use client";

import { useState, useEffect, useRef } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Image as ImageIcon, Loader2, X, Users, User, Globe, Bell, Calendar, LayoutGrid, Video } from "lucide-react";
import { getCookie, cn } from "@/lib/utils";

interface Metadata {
  center_id: string;
  center_name: string;
  groups: { id: string; name: string }[];
  parents: { id: string; name: string }[];
}

interface MentionUser {
  id: string;
  name: string;
  profile_photo: string | null;
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

  // Mention State
  const [mentionQuery, setMentionQuery] = useState("");
  const [mentionResults, setMentionResults] = useState<MentionUser[]>([]);
  const [showMentionList, setShowMentionList] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

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

  useEffect(() => {
    if (!mentionQuery) {
      setMentionResults([]);
      setShowMentionList(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`http://localhost:8001/chat/search-users/?q=${mentionQuery}`, { credentials: 'include' });
        const data = await res.json();
        setMentionResults(data.users || []);
        setShowMentionList(true);
      } catch (err) {
        console.error("Failed to fetch mentions", err);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [mentionQuery]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newVal = e.target.value;
    setContent(newVal);

    const match = newVal.match(/@([\w\s]*)$/);
    if (match) {
      setMentionQuery(match[1]);
    } else {
      setMentionQuery("");
      setShowMentionList(false);
    }
  };

  const insertMention = (user: MentionUser) => {
    // Use @[Name] format for precise parsing
    const newVal = content.replace(/@([\w\s]*)$/, `@[${user.name}] `);
    setContent(newVal);
    setShowMentionList(false);
    setMentionQuery("");
    inputRef.current?.focus();
  };

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
      <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col p-0 overflow-hidden rounded-2xl shadow-2xl border-0">
        <DialogHeader className="px-8 pt-8 pb-4 bg-background">
          <DialogTitle className="text-2xl font-bold tracking-tight">New Announcement</DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto px-8 py-2 space-y-8 scrollbar-hide relative">
          {/* Center Selection */}
          {metadata.length > 1 && (
            <div className="space-y-3">
              <label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/70">Select Center</label>
              <select 
                className="w-full p-3 rounded-xl border bg-muted/30 text-sm focus:ring-2 focus:ring-primary/20 outline-none transition-all cursor-pointer hover:bg-muted/50"
                value={selectedCenter}
                onChange={(e) => setSelectedCenter(e.target.value)}
              >
                {metadata.map(m => (
                  <option key={m.center_id} value={m.center_id}>{m.center_name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Visibility Segmented Control */}
          <div className="space-y-3">
            <label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/70">Audience</label>
            <Tabs value={visibility} onValueChange={(v: any) => setVisibility(v)} className="w-full">
              <TabsList className="w-full h-12 bg-muted/40 p-1.5 rounded-xl border border-muted/50">
                <TabsTrigger value="all_parents" className="flex-1 gap-2 rounded-lg data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-md transition-all">
                  <Globe className="h-4 w-4" />
                  <span className="text-xs font-semibold">All Parents</span>
                </TabsTrigger>
                <TabsTrigger value="specific_groups" className="flex-1 gap-2 rounded-lg data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-md transition-all">
                  <Users className="h-4 w-4" />
                  <span className="text-xs font-semibold">Groups</span>
                </TabsTrigger>
                <TabsTrigger value="specific_parents" className="flex-1 gap-2 rounded-lg data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-md transition-all">
                  <User className="h-4 w-4" />
                  <span className="text-xs font-semibold">Specific</span>
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          {/* Target Selection Areas (Conditional) */}
          {(visibility === "specific_groups" || visibility === "specific_parents") && (
            <div className="space-y-4 p-4 rounded-2xl bg-muted/20 border border-muted/50 animate-in fade-in slide-in-from-top-2 duration-300">
              {visibility === "specific_groups" && currentCenterMetadata && (
                <div className="space-y-3">
                  <label className="text-xs font-bold text-muted-foreground">Select Target Groups</label>
                  <div className="flex flex-wrap gap-2">
                    {currentCenterMetadata.groups.map(g => (
                      <button
                        key={g.id}
                        onClick={() => setSelectedGroups(prev => prev.includes(g.id) ? prev.filter(id => id !== g.id) : [...prev, g.id])}
                        className={cn(
                          "px-4 py-2 rounded-xl text-xs font-semibold border transition-all",
                          selectedGroups.includes(g.id) 
                            ? "bg-primary text-primary-foreground border-primary shadow-sm scale-105" 
                            : "bg-background hover:bg-muted border-muted-foreground/10"
                        )}
                      >
                        {g.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {visibility === "specific_parents" && currentCenterMetadata && (
                <div className="space-y-3">
                  <label className="text-xs font-bold text-muted-foreground">Select Individual Parents</label>
                  <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto p-1">
                    {currentCenterMetadata.parents.map(p => (
                      <button
                        key={p.id}
                        onClick={() => setSelectedParents(prev => prev.includes(p.id) ? prev.filter(id => id !== p.id) : [...prev, p.id])}
                        className={cn(
                          "px-4 py-2 rounded-xl text-xs font-semibold border transition-all",
                          selectedParents.includes(p.id) 
                            ? "bg-primary text-primary-foreground border-primary shadow-sm scale-105" 
                            : "bg-background hover:bg-muted border-muted-foreground/10"
                        )}
                      >
                        {p.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Message Area */}
          <div className="space-y-3 relative">
            <label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/70">Message</label>
            
            {showMentionList && mentionResults.length > 0 && (
              <div className="absolute bottom-full left-0 mb-2 w-64 bg-background border rounded-lg shadow-lg overflow-hidden z-50 animate-in fade-in slide-in-from-bottom-2">
                <ScrollArea className="max-h-48">
                  <div className="p-1">
                    <div className="px-2 py-1.5 text-[10px] font-bold text-muted-foreground uppercase tracking-wider border-b mb-1">Suggested People</div>
                    {mentionResults.map(user => (
                      <button
                        key={user.id}
                        className="flex items-center gap-2 w-full p-2 hover:bg-muted text-left text-sm rounded-md transition-colors group"
                        onClick={() => insertMention(user)}
                      >
                        <Avatar className="h-7 w-7 border group-hover:border-primary/30 transition-colors">
                          <AvatarImage src={user.profile_photo || undefined} />
                          <AvatarFallback>{user.name[0]}</AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <p className="font-bold truncate group-hover:text-primary transition-colors text-xs">{user.name}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}

            <Textarea 
              ref={inputRef}
              placeholder="What would you like to share? Use @ to mention someone." 
              className="min-h-[140px] resize-none rounded-2xl border-muted/60 focus:ring-2 focus:ring-primary/10 p-5 text-sm leading-relaxed shadow-inner"
              value={content}
              onChange={handleInputChange}
            />
          </div>

          {/* Media Previews (1:1 Aspect Ratio) */}
          {mediaFiles.length > 0 && (
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-4">
              {mediaFiles.map((media, index) => (
                <div key={index} className="relative rounded-2xl overflow-hidden border border-muted/50 bg-muted aspect-square group shadow-md transition-transform hover:scale-[1.02]">
                  {media.type === 'image' ? (
                    <img src={media.preview} alt={`Preview ${index}`} className="w-full h-full object-cover" />
                  ) : (
                    <video src={media.preview} className="w-full h-full object-cover" />
                  )}
                  <button
                    className="absolute top-2 right-2 h-7 w-7 rounded-full bg-black/70 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all hover:bg-black/90 shadow-xl"
                    onClick={() => removeMedia(index)}
                  >
                    <X className="h-4 w-4" strokeWidth={3} />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Footer Controls / Tag Selector */}
          <div className="flex flex-col gap-6 pb-8">
            <div className="flex flex-wrap gap-2">
              {[
                { id: 'announcements', label: 'Announcement', icon: Bell },
                { id: 'photos', label: 'Photo', icon: ImageIcon },
                { id: 'videos', label: 'Video', icon: Video },
                { id: 'events', label: 'Event', icon: Calendar },
              ].map((tag) => (
                <button
                  key={tag.id}
                  onClick={() => toggleTag(tag.id)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold border transition-all",
                    tags.includes(tag.id)
                      ? "bg-primary/10 text-primary border-primary/20"
                      : "bg-muted/30 hover:bg-muted border-transparent text-muted-foreground/70"
                  )}
                >
                  <tag.icon className="h-3.5 w-3.5" />
                  {tag.label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-3">
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
                className="flex-1 rounded-2xl h-14 border-dashed border-muted-foreground/30 hover:border-primary hover:text-primary hover:bg-primary/5 transition-all text-sm font-bold gap-3"
                onClick={() => document.getElementById('post-media')?.click()}
              >
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <ImageIcon className="h-4 w-4 text-primary" />
                </div>
                Attach Photos or Videos
              </Button>
            </div>
          </div>
        </div>

        <DialogFooter className="px-8 py-6 bg-muted/10 border-t flex items-center sm:justify-between gap-4">
          <Button variant="ghost" onClick={onClose} className="rounded-xl px-6 h-12 font-bold text-muted-foreground hover:text-foreground">
            Cancel
          </Button>
          <Button 
            disabled={isLoading || (!content.trim() && mediaFiles.length === 0)} 
            onClick={handleSubmit}
            className="flex-1 sm:flex-none px-10 h-12 rounded-xl shadow-lg shadow-primary/20 font-bold tracking-tight transition-all active:scale-95"
          >
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : "Post Announcement"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
