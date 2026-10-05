"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { 
  Heart, 
  MessageCircle, 
  Share2, 
  MoreHorizontal, 
  Plus, 
  Loader2, 
  Send,
  Globe,
  Users,
  User,
  Eye,
  LayoutGrid,
  ImageIcon,
  Video,
  Trash2,
  Calendar
} from "lucide-react";
import { CreatePostDialog } from "@/components/create-post-dialog";
import { MediaPreview } from "@/components/media-preview";
import { getCookie, cn } from "@/lib/utils";

// --- Types ---
interface Post {
  id: number;
  author: {
    id: string;
    name: string;
    role: string;
    profile_photo: string | null;
  };
  content: string;
  image: string | null;
  media?: { url: string; type: 'image' | 'video' }[];
  tags?: string[];
  visibility: string;
  target_group_names: string[];
  timestamp: string;
  reactions_count: number;
  comments_count: number;
  views_count?: number;
  user_reaction: string | null;
  center_name: string;
}

interface Comment {
  id: number;
  author: {
    id: string;
    name: string;
    profile_photo: string | null;
  };
  content: string;
  timestamp: string;
  reactions_count: number;
}

// --- Feed Stream Component ---
interface FeedStreamProps {
  currentUser: any;
  filter: string;
  searchQuery?: string;
  onPersonClick?: (contact: any) => void;
}

export function FeedStream({ currentUser, filter, searchQuery = "", onPersonClick }: FeedStreamProps) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [matchingUsers, setMatchingUsers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isPeopleLoading, setIsPeopleLoading] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  
  const observerTarget = useRef<HTMLDivElement>(null);

  const fetchPosts = useCallback(async (pageNum: number = 1, currentFilter: string, q: string = "") => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: pageNum.toString(),
        type: currentFilter,
        q: q
      });
      const res = await fetch(`http://localhost:8001/chat/feed/?${params.toString()}`, { credentials: 'include' });
      const data = await res.json();
      if (pageNum === 1) {
        setPosts(data.posts || []);
      } else {
        setPosts(prev => [...prev, ...(data.posts || [])]);
      }
      setHasMore(data.has_next);
    } catch (err) {
      console.error("Failed to fetch feed", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchPeople = useCallback(async (q: string) => {
    if (!q || q.length < 2) {
      setMatchingUsers([]);
      return;
    }
    setIsPeopleLoading(true);
    try {
      const res = await fetch(`http://localhost:8001/chat/search-users/?q=${q}`, { credentials: 'include' });
      const data = await res.json();
      setMatchingUsers(data.users || []);
    } catch (err) {
      console.error("Failed to fetch people", err);
    } finally {
      setIsPeopleLoading(false);
    }
  }, []);

  useEffect(() => {
    setPage(1);
    fetchPosts(1, filter, searchQuery);
    if (searchQuery) {
      fetchPeople(searchQuery);
    } else {
      setMatchingUsers([]);
    }
  }, [fetchPosts, fetchPeople, filter, searchQuery]);

  // Infinite Scroll Observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !isLoading) {
          setPage(prev => {
            const next = prev + 1;
            fetchPosts(next, filter, searchQuery);
            return next;
          });
        }
      },
      { threshold: 1.0 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => observer.disconnect();
  }, [hasMore, isLoading, fetchPosts, filter, searchQuery]);

  const canCreatePost = currentUser?.role && ['director', 'vice_director', 'educator', 'owner'].includes(currentUser.role);

  return (
    <div className="flex-1 max-w-[680px] w-full min-w-0 mx-auto py-6 space-y-6">
      
      {/* Create Post Card */}
      {canCreatePost && !searchQuery && (
        <div className="bg-background rounded-2xl border shadow-sm p-4 animate-in fade-in slide-in-from-top-2 duration-500">
          <div className="flex gap-3">
            <Avatar className="h-10 w-10">
              <AvatarImage src={currentUser?.profile_photo || undefined} />
              <AvatarFallback>{currentUser?.name?.[0] || "U"}</AvatarFallback>
            </Avatar>
            <button 
              onClick={() => setIsCreateDialogOpen(true)}
              className="flex-1 bg-muted/50 hover:bg-muted text-left px-4 py-2.5 rounded-full text-sm text-muted-foreground transition-colors"
            >
              What's happening at the center, {currentUser?.name?.split(' ')[0]}?
            </button>
          </div>
          <div className="border-t mt-4 pt-3 flex justify-between px-2">
            <Button variant="ghost" size="sm" className="gap-2 text-muted-foreground hover:bg-muted/50" onClick={() => setIsCreateDialogOpen(true)}>
              <ImageIcon className="h-5 w-5 text-emerald-500" />
              <span className="font-medium text-xs">Photo</span>
            </Button>
            <Button variant="ghost" size="sm" className="gap-2 text-muted-foreground hover:bg-muted/50" onClick={() => setIsCreateDialogOpen(true)}>
              <Video className="h-5 w-5 text-blue-500" />
              <span className="font-medium text-xs">Video</span>
            </Button>
            <Button variant="ghost" size="sm" className="gap-2 text-muted-foreground hover:bg-muted/50" onClick={() => setIsCreateDialogOpen(true)}>
              <Calendar className="h-5 w-5 text-rose-500" />
              <span className="font-medium text-xs">Event</span>
            </Button>
          </div>
        </div>
      )}

      {/* Search Header & Results */}
      {searchQuery && (
        <div className="space-y-6 animate-in fade-in duration-500">
          <div className="px-2">
            <h2 className="text-xl font-bold text-foreground tracking-tight">Search results for "{searchQuery}"</h2>
          </div>

          {/* People Section */}
          {(isPeopleLoading || matchingUsers.length > 0) && (
            <div className="bg-background rounded-2xl border shadow-sm p-4 space-y-4">
              <div className="flex items-center justify-between px-2">
                <h3 className="font-bold text-sm text-muted-foreground uppercase tracking-wider">People</h3>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {isPeopleLoading ? (
                  Array(2).fill(0).map((_, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 animate-pulse bg-muted/20 rounded-xl">
                      <div className="w-12 h-12 bg-muted rounded-full" />
                      <div className="space-y-2 flex-1">
                        <div className="h-3 bg-muted rounded w-3/4" />
                        <div className="h-2 bg-muted rounded w-1/2" />
                      </div>
                    </div>
                  ))
                ) : (
                  matchingUsers.slice(0, 4).map((user) => (
                    <div 
                      key={user.id} 
                      className="flex items-center gap-3 p-3 hover:bg-muted/50 rounded-xl border border-transparent hover:border-border transition-all cursor-pointer group"
                      onClick={() => onPersonClick?.(user)}
                    >
                      <Avatar className="h-12 w-12 shadow-sm ring-2 ring-background">
                        <AvatarImage src={user.profile_photo} className="object-cover" />
                        <AvatarFallback>{user.name[0]}</AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="font-bold text-sm truncate group-hover:text-primary transition-colors">{user.name}</p>
                        <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-tight">{user.role.replace('_', ' ')}</p>
                      </div>
                      <Button variant="outline" size="sm" className="rounded-full h-8 px-4 text-[10px] font-bold uppercase tracking-widest pointer-events-none">Message</Button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Posts Stream */}
      <div className="space-y-6">
        {posts.map(post => (
          <FeedPostCard key={post.id} post={post} currentUser={currentUser} />
        ))}
        
        {isLoading && (
          <div className="flex justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}

        {!isLoading && posts.length === 0 && (
          <div className="bg-background rounded-2xl border shadow-sm p-12 text-center space-y-4">
            <div className="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mx-auto">
              <LayoutGrid className="h-8 w-8 text-muted-foreground" />
            </div>
            <div className="space-y-1">
              <h3 className="font-bold text-lg">No posts yet</h3>
              <p className="text-muted-foreground text-sm">Check back later or change your filter.</p>
            </div>
          </div>
        )}

        {/* Observer Target for Infinite Scroll */}
        <div ref={observerTarget} className="h-10 w-full" />
      </div>

      <CreatePostDialog 
        isOpen={isCreateDialogOpen} 
        onClose={() => setIsCreateDialogOpen(false)}
        onSuccess={() => {
          setPage(1);
          fetchPosts(1, filter, searchQuery);
        }}
      />
    </div>
  );
}

// --- Helper Components ---

function FeedPostCard({ post, currentUser }: { post: Post, currentUser: any }) {
  const [isLiked, setIsLiked] = useState(post.user_reaction === 'like');
  const [likesCount, setLikesCount] = useState(post.reactions_count);
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState<Comment[]>([]);
  const [isCommentsLoading, setIsCommentsLoading] = useState(false);
  const [isDeleted, setIsDeleted] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [currentMediaIndex, setCurrentMediaIndex] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetch(`http://localhost:8001/chat/feed/${post.id}/seen/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie('csrftoken') || "" },
        credentials: 'include',
      }).catch(err => console.error("Failed to mark post as seen", err));
    }, 2000);
    return () => clearTimeout(timer);
  }, [post.id]);

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this post?")) return;
    
    try {
      const res = await fetch(`http://localhost:8001/chat/feed/${post.id}/delete/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie('csrftoken') || "" },
        credentials: 'include',
      });
      if (res.ok) {
        setIsDeleted(true);
      } else {
        console.error("Failed to delete post");
      }
    } catch (err) {
      console.error("Failed to delete post", err);
    }
  };

  const handleLike = async () => {
    const newLiked = !isLiked;
    setIsLiked(newLiked);
    setLikesCount(prev => newLiked ? prev + 1 : prev - 1);

    try {
      await fetch(`http://localhost:8001/chat/feed/${post.id}/react/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie('csrftoken') || "" },
        credentials: 'include',
      });
    } catch (err) {
      console.error("Failed to react", err);
      setIsLiked(!newLiked);
      setLikesCount(prev => !newLiked ? prev + 1 : prev - 1);
    }
  };

  const fetchComments = async () => {
    if (showComments) {
      setShowComments(false);
      return;
    }
    
    setShowComments(true);
    setIsCommentsLoading(true);
    try {
      const res = await fetch(`http://localhost:8001/chat/feed/${post.id}/comments/`, { credentials: 'include' });
      const data = await res.json();
      setComments(data.comments || []);
    } catch (err) {
      console.error("Failed to fetch comments", err);
    } finally {
      setIsCommentsLoading(false);
    }
  };

  const isStaff = currentUser?.role && ['director', 'vice_director', 'educator', 'owner'].includes(currentUser.role);

  if (isDeleted) return null;

  return (
    <div className="bg-background rounded-2xl border shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="p-4 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Avatar className="h-10 w-10 ring-2 ring-muted/50 cursor-pointer">
            <AvatarImage src={post.author.profile_photo || undefined} className="object-cover" />
            <AvatarFallback>{post.author.name[0]}</AvatarFallback>
          </Avatar>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm hover:underline cursor-pointer">{post.author.name}</span>
              <span className="text-[10px] bg-muted px-2 py-0.5 rounded-full uppercase font-bold tracking-wider text-muted-foreground">
                {post.author.role.replace('_', ' ')}
              </span>
            </div>
            <div className="flex flex-col gap-1 mt-0.5">
              <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                <span className="hover:underline cursor-pointer">
                  {new Date(post.timestamp).toLocaleDateString()} at {new Date(post.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                <span>•</span>
                {post.visibility === 'all_parents' && <Globe className="h-3 w-3" />}
                {post.visibility === 'specific_groups' && <Users className="h-3 w-3" />}
                {post.visibility === 'specific_parents' && <User className="h-3 w-3" />}
              </div>
            </div>
          </div>
        </div>
        {currentUser?.id === post.author.id || isStaff ? (
          <Button variant="ghost" size="icon" className="rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive -mt-1" onClick={handleDelete} title="Delete Post">
            <Trash2 className="h-5 w-5" />
          </Button>
        ) : (
          <Button variant="ghost" size="icon" className="rounded-full text-muted-foreground -mt-1">
            <MoreHorizontal className="h-5 w-5" />
          </Button>
        )}
      </div>

      <div className="px-4 pb-4 space-y-4">
        <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground/90">{post.content}</p>
        
        {post.media && post.media.length > 0 ? (
          <div className="space-y-2">
            <div className={cn(
              "grid gap-1 rounded-xl overflow-hidden border bg-muted/10",
              post.media.length === 1 ? "grid-cols-1" : 
              post.media.length === 2 ? "grid-cols-2" : 
              post.media.length === 3 ? "grid-cols-2" :
              "grid-cols-2"
            )}>
              {post.media.slice(0, 4).map((mediaItem, index) => {
                const totalCount = post.media!.length;
                const isLastVisible = index === 3 && totalCount > 4;
                let gridClass = "relative group cursor-zoom-in hover:opacity-95 transition-all bg-muted/20 overflow-hidden";
                
                if (totalCount === 1) gridClass += " w-full";
                else if (totalCount === 2) gridClass += " aspect-[4/5]";
                else if (totalCount === 3) {
                  if (index === 0) gridClass += " row-span-2 aspect-[4/5]";
                  else gridClass += " aspect-square";
                } else gridClass += " aspect-square";

                return (
                  <div 
                    key={index} 
                    className={gridClass}
                    onClick={() => {
                      setCurrentMediaIndex(index);
                      setIsPreviewOpen(true);
                    }}
                  >
                    {mediaItem.type === 'image' ? (
                      <img 
                        src={mediaItem.url} 
                        alt={`Post media ${index}`} 
                        className="w-full h-full object-cover select-none pointer-events-none" 
                        onContextMenu={(e) => e.preventDefault()}
                      />
                    ) : (
                      <div className="relative w-full h-full">
                        <video src={mediaItem.url} className="w-full h-full object-cover" />
                        <div className="absolute inset-0 flex items-center justify-center bg-black/10 group-hover:bg-black/20 transition-colors">
                          <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/30">
                            <Video className="w-6 h-6 text-white fill-current" />
                          </div>
                        </div>
                      </div>
                    )}
                    
                    <div className="absolute inset-0 z-10 select-none" onContextMenu={(e) => e.preventDefault()} />

                    {isLastVisible && (
                      <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center backdrop-blur-[3px] z-20 transition-colors group-hover:bg-black/50">
                        <span className="text-white text-3xl font-black tracking-tight">+{totalCount - 3}</span>
                        <span className="text-white/80 text-[10px] font-bold uppercase tracking-widest mt-1">Photos</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ) : post.image ? (
          <div 
            className="rounded-xl overflow-hidden border bg-muted/20 relative group cursor-zoom-in hover:opacity-95 transition-opacity"
            onClick={() => {
              setCurrentMediaIndex(0);
              setIsPreviewOpen(true);
            }}
          >
            <img 
              src={post.image} 
              alt="Post" 
              className="w-full h-auto max-h-[600px] object-contain mx-auto select-none" 
              onContextMenu={(e) => e.preventDefault()}
            />
          </div>
        ) : null}
      </div>

      {isStaff && post.views_count !== undefined && (
        <div className="px-4 py-2 border-t border-b flex items-center justify-between text-xs text-muted-foreground bg-muted/5">
           <div className="flex items-center gap-1">
             {post.reactions_count > 0 && (
               <div className="flex items-center gap-1">
                 <div className="bg-red-500 rounded-full p-1"><Heart className="h-2 w-2 text-white fill-current" /></div>
                 <span>{post.reactions_count}</span>
               </div>
             )}
           </div>
           <div className="flex items-center gap-4">
             <span>{post.comments_count} comments</span>
             <span className="flex items-center gap-1"><Eye className="h-3.5 w-3.5" /> {post.views_count} views</span>
           </div>
        </div>
      )}

      <div className="px-2 py-1 grid grid-cols-3 gap-1">
        <Button 
          variant="ghost" 
          size="sm" 
          className={cn("gap-2 rounded-lg h-10 hover:bg-muted font-medium text-muted-foreground", isLiked && "text-red-500 hover:text-red-600 hover:bg-red-50")}
          onClick={handleLike}
        >
          <Heart className={cn("h-5 w-5 transition-all", isLiked && "fill-current scale-110")} />
          Like
        </Button>
        <Button 
          variant="ghost" 
          size="sm" 
          className="gap-2 rounded-lg h-10 hover:bg-muted font-medium text-muted-foreground"
          onClick={fetchComments}
        >
          <MessageCircle className="h-5 w-5" />
          Comment
        </Button>
        <Button 
          variant="ghost" 
          size="sm" 
          className="gap-2 rounded-lg h-10 hover:bg-muted font-medium text-muted-foreground"
        >
          <Share2 className="h-5 w-5" />
          Share
        </Button>
      </div>

      <MediaPreview
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        mediaItems={post.media || (post.image ? [{ url: post.image, type: 'image', id: 'single' }] : [])}
        currentIndex={currentMediaIndex}
        onIndexChange={setCurrentMediaIndex}
      />

      {showComments && (
        <div className="border-t bg-muted/5 p-4 space-y-4 animate-in slide-in-from-top-2 duration-300">
          <CommentInput postId={post.id} onCommentAdded={(newComment) => {
            setComments(prev => [...prev, {
              id: newComment.id,
              author: {
                id: currentUser.id,
                name: currentUser.name,
                profile_photo: currentUser.profile_photo
              },
              content: newComment.content,
              timestamp: newComment.timestamp,
              reactions_count: 0
            }]);
          }} currentUser={currentUser} />

          <div className="space-y-4 pt-2">
            {isCommentsLoading ? (
              <div className="flex justify-center py-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
              </div>
            ) : (
              comments.map(comment => (
                <div key={comment.id} className="flex gap-2.5">
                  <Avatar className="h-8 w-8 shrink-0 cursor-pointer">
                    <AvatarImage src={comment.author.profile_photo || undefined} className="object-cover" />
                    <AvatarFallback>{comment.author.name[0]}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1 group">
                    <div className="bg-muted/40 p-3 rounded-2xl rounded-tl-none inline-block min-w-[150px]">
                      <div className="font-bold text-xs hover:underline cursor-pointer">{comment.author.name}</div>
                      <p className="text-sm leading-relaxed">{comment.content}</p>
                    </div>
                    <div className="flex items-center gap-3 px-2 mt-1 text-[11px] text-muted-foreground font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                      <span>{new Date(comment.timestamp).toLocaleDateString()}</span>
                      <button className="hover:underline">Like</button>
                      <button className="hover:underline">Reply</button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function CommentInput({ postId, onCommentAdded, currentUser }: { postId: number, onCommentAdded: (c: any) => void, currentUser: any }) {
  const [content, setContent] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAddComment = async () => {
    if (!content.trim()) return;
    setIsSubmitting(true);

    try {
      const res = await fetch(`http://localhost:8001/chat/feed/${postId}/comments/add/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": getCookie('csrftoken') || "",
        },
        body: new URLSearchParams({ content }),
        credentials: 'include',
      });
      const data = await res.json();
      if (res.ok) {
        onCommentAdded(data.comment);
        setContent("");
      }
    } catch (err) {
      console.error("Failed to add comment", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative flex gap-2">
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarImage src={currentUser?.profile_photo || undefined} />
        <AvatarFallback>{currentUser?.name?.[0] || "U"}</AvatarFallback>
      </Avatar>
      
      <div className="flex-1 relative">
        <Textarea 
          placeholder="Write a comment..." 
          className="min-h-[40px] max-h-32 py-2.5 pr-10 resize-none text-sm rounded-2xl bg-muted/30 border-transparent focus:bg-background focus:border-input focus:ring-1 focus:ring-primary transition-all"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleAddComment();
            }
          }}
        />
        <button 
          className="absolute right-2 top-2 p-1 text-primary hover:bg-primary/10 rounded-full transition-colors disabled:opacity-50"
          disabled={!content.trim() || isSubmitting}
          onClick={handleAddComment}
        >
          {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}
