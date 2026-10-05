"use client";

import { useState, useEffect, useCallback } from "react";
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
  AtSign,
  Globe,
  Users,
  User,
  Eye,
  Download,
  LayoutGrid,
  Bell,
  Calendar,
  Image as ImageIcon,
  Video,
  Trash2,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { CreatePostDialog } from "./create-post-dialog";
import { MediaPreview } from "./media-preview";
import { getCookie, cn } from "@/lib/utils";

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

export function FeedView({ currentUser, activeFeedFilter = "all" }: { currentUser: any, activeFeedFilter?: string }) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const fetchPosts = useCallback(async (pageNum: number = 1, filter: string = activeFeedFilter) => {
    setIsLoading(true);
    try {
      const res = await fetch(`http://localhost:8001/chat/feed/?page=${pageNum}&type=${filter}`, { credentials: 'include' });
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
  }, [activeFeedFilter]);

  useEffect(() => {
    setPage(1);
    fetchPosts(1, activeFeedFilter);
  }, [fetchPosts, activeFeedFilter]);

  const canCreatePost = currentUser?.role && ['director', 'vice_director', 'educator', 'owner'].includes(currentUser.role);

  return (
    <div className="flex flex-col h-full overflow-hidden bg-muted/5 relative items-center">
      {/* Feed Header */}
      <div className="bg-background border-b px-6 h-16 flex items-center justify-between shadow-sm sticky top-0 z-20 w-full">
        <div className="flex items-center gap-2 max-w-2xl mx-auto w-full">
          <div className="flex items-center gap-2 flex-1">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <LayoutGrid className="w-5 h-5 text-primary-foreground" />
            </div>
            <h2 className="font-bold text-xl tracking-tight">Center Feed</h2>
          </div>
          
          {canCreatePost && (
            <Button onClick={() => setIsCreateDialogOpen(true)} className="gap-2 shadow-md">
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">New Post</span>
            </Button>
          )}
        </div>
      </div>

      <div className="flex-1 min-h-0 w-full">
        <ScrollArea className="h-full w-full">
          <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
            {posts.map(post => (
            <FeedPostCard key={post.id} post={post} currentUser={currentUser} />
          ))}
          
          {isLoading && (
            <div className="flex justify-center py-4">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          )}

          {!isLoading && posts.length === 0 && (
            <div className="text-center py-20 space-y-4">
              <div className="w-20 h-20 bg-muted rounded-full flex items-center justify-center mx-auto">
                <MessageCircle className="h-10 w-10 text-muted-foreground" />
              </div>
              <div className="space-y-1">
                <h3 className="font-bold text-lg">No posts yet</h3>
                <p className="text-muted-foreground">Announcements from your center will appear here.</p>
              </div>
            </div>
          )}

          {hasMore && !isLoading && (
            <Button 
              variant="ghost" 
              className="w-full" 
              onClick={() => {
                const nextPage = page + 1;
                setPage(nextPage);
                fetchPosts(nextPage);
              }}
            >
              Load More
            </Button>
          )}
        </div>
        </ScrollArea>
      </div>

      <CreatePostDialog 
        isOpen={isCreateDialogOpen} 
        onClose={() => setIsCreateDialogOpen(false)}
        onSuccess={() => {
          setPage(1);
          fetchPosts(1);
        }}
      />
    </div>
  );
}

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
    // Mark post as seen after 2 seconds of viewing
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

  return (
    <div className="bg-background rounded-2xl border shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Post Header */}
      <div className="p-4 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Avatar className="h-10 w-10 ring-2 ring-muted/50">
            <AvatarImage src={post.author.profile_photo || undefined} className="object-cover" />
            <AvatarFallback>{post.author.name[0]}</AvatarFallback>
          </Avatar>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm">{post.author.name}</span>
              <span className="text-[10px] bg-muted px-2 py-0.5 rounded-full uppercase font-bold tracking-wider text-muted-foreground">
                {post.author.role.replace('_', ' ')}
              </span>
            </div>
            <div className="flex flex-col gap-1.5 mt-1">
              <span className="text-[10px] text-muted-foreground font-medium">
                {new Date(post.timestamp).toLocaleDateString()} at {new Date(post.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
              
              <div className="flex items-center gap-1.5 flex-wrap">
                {/* Toned down Visibility & Tags */}
                <div className="flex items-center gap-1.5 text-[9px] font-bold text-muted-foreground tracking-tight uppercase">
                  {post.visibility === 'all_parents' && (
                    <span className="flex items-center gap-1">
                      <Globe className="h-3 w-3" />
                      Center
                    </span>
                  )}
                  {post.visibility === 'specific_groups' && (
                    <span className="flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      {post.target_group_names.join(', ')}
                    </span>
                  )}
                  {post.visibility === 'specific_parents' && (
                    <span className="flex items-center gap-1">
                      <User className="h-3 w-3" />
                      Private
                    </span>
                  )}

                  {post.tags && post.tags.filter(t => t !== 'general').map((tag, idx) => (
                    <span key={idx} className="flex items-center gap-1 before:content-['•'] before:mx-1 before:opacity-50">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
        {currentUser?.id === post.author.id || isStaff ? (
          <Button variant="ghost" size="icon" className="rounded-full text-destructive hover:bg-destructive/10 hover:text-destructive -mt-1" onClick={handleDelete} title="Delete Post">
            <Trash2 className="h-5 w-5" />
          </Button>
        ) : (
          <Button variant="ghost" size="icon" className="rounded-full text-muted-foreground -mt-1">
            <MoreHorizontal className="h-5 w-5" />
          </Button>
        )}
      </div>

      {/* Post Content */}
      <div className="px-4 pb-4 space-y-4">
        <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground/90">{post.content}</p>
        
        {post.media && post.media.length > 0 ? (
          <div className="space-y-2">
            <div className={cn(
              "grid gap-2",
              post.media.length === 1 ? "grid-cols-1" : 
              post.media.length === 2 ? "grid-cols-2" : 
              "grid-cols-2 md:grid-cols-2"
            )}>
              {post.media.slice(0, 4).map((mediaItem, index) => {
                const isLastVisible = index === 3 && post.media!.length > 4;
                return (
                  <div 
                    key={index} 
                    className="rounded-xl overflow-hidden border bg-muted/20 relative group aspect-square cursor-zoom-in hover:opacity-95 transition-opacity"
                    onClick={() => {
                      setCurrentMediaIndex(index);
                      setIsPreviewOpen(true);
                    }}
                  >
                    {mediaItem.type === 'image' ? (
                      <img 
                        src={mediaItem.url} 
                        alt={`Post media ${index}`} 
                        className="w-full h-full object-cover select-none" 
                        onContextMenu={(e) => e.preventDefault()}
                      />
                    ) : (
                      <div className="relative w-full h-full">
                        <video src={mediaItem.url} className="w-full h-full object-cover" />
                        <div className="absolute inset-0 flex items-center justify-center bg-black/10 group-hover:bg-black/20 transition-colors">
                          <Video className="w-10 h-10 text-white/80" />
                        </div>
                      </div>
                    )}
                    
                    {isLastVisible && (
                      <div className="absolute inset-0 bg-black/60 flex items-center justify-center backdrop-blur-[2px]">
                        <span className="text-white text-xl font-bold">+{post.media!.length - 3}</span>
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
              className="w-full h-auto max-h-[500px] object-contain mx-auto select-none" 
              onContextMenu={(e) => e.preventDefault()}
            />
          </div>
        ) : null}
      </div>

      {/* Read Receipts for Staff */}
      {isStaff && post.views_count !== undefined && (
        <div className="px-4 py-1 flex items-center gap-1.5 text-[10px] font-bold text-muted-foreground/60 uppercase tracking-wider">
          <Eye className="h-3.5 w-3.5" />
          Seen by {post.views_count} parents
        </div>
      )}

      {/* Post Actions */}
      <div className="px-4 py-2 border-t flex items-center justify-between bg-muted/5">
        <div className="flex items-center gap-1">
          <Button 
            variant="ghost" 
            size="sm" 
            className={cn("gap-2 rounded-full px-4 h-9", isLiked && "text-red-500 hover:text-red-600 hover:bg-red-50 bg-red-50/30")}
            onClick={handleLike}
          >
            <Heart className={cn("h-4 w-4 transition-all", isLiked && "fill-current scale-110")} />
            <span className="text-xs font-bold">{likesCount}</span>
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            className="gap-2 rounded-full px-4 h-9"
            onClick={fetchComments}
          >
            <MessageCircle className="h-4 w-4" />
            <span className="text-xs font-bold">{post.comments_count}</span>
          </Button>
        </div>
        
        <div />
        </div>

        {/* Media Preview Overlay */}
        <MediaPreview
          isOpen={isPreviewOpen}
          onClose={() => setIsPreviewOpen(false)}
          mediaItems={post.media || (post.image ? [{ url: post.image, type: 'image', id: 'single' }] : [])}
          currentIndex={currentMediaIndex}
          onIndexChange={setCurrentMediaIndex}
        />

        {/* Comments Section */}      {showComments && (
        <div className="border-t bg-muted/10 p-4 space-y-4 animate-in slide-in-from-top-2 duration-300">
          <div className="space-y-4">
            {isCommentsLoading ? (
              <div className="flex justify-center py-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
              </div>
            ) : (
              comments.map(comment => (
                <div key={comment.id} className="flex gap-3">
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarImage src={comment.author.profile_photo || undefined} className="object-cover" />
                    <AvatarFallback>{comment.author.name[0]}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1 space-y-1">
                    <div className="bg-background p-3 rounded-2xl shadow-sm border">
                      <div className="font-bold text-xs mb-1">{comment.author.name}</div>
                      <p className="text-xs leading-relaxed">{comment.content}</p>
                    </div>
                    <div className="flex items-center gap-3 px-2 text-[10px] text-muted-foreground">
                      <span className="font-medium">{new Date(comment.timestamp).toLocaleDateString()}</span>
                      <button className="font-bold hover:text-primary transition-colors">Like</button>
                      <button className="font-bold hover:text-primary transition-colors">Reply</button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Add Comment Input */}
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
          }} />
        </div>
      )}
    </div>
  );
}

function CommentInput({ postId, onCommentAdded }: { postId: number, onCommentAdded: (c: any) => void }) {
  const [content, setContent] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showMentions, setShowMentions] = useState(false);
  const [contacts, setContacts] = useState<any[]>([]);

  // Simple mention logic
  useEffect(() => {
    if (content.endsWith("@")) {
      fetch("http://localhost:8001/chat/contacts/", { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
          setContacts(data.contacts || []);
          setShowMentions(true);
        });
    } else if (!content.includes("@")) {
      setShowMentions(false);
    }
  }, [content]);

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
    <div className="relative">
      {showMentions && (
        <div className="absolute bottom-full left-0 w-64 bg-background border rounded-lg shadow-xl mb-2 z-50 overflow-hidden animate-in fade-in slide-in-from-bottom-2">
          <div className="p-2 border-b bg-muted/30 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Mention someone</div>
          <ScrollArea className="max-h-40">
            <div className="flex flex-col">
              {contacts.map(contact => (
                <button
                  key={contact.id}
                  onClick={() => {
                    setContent(prev => prev.substring(0, prev.lastIndexOf("@")) + "@" + contact.name + " ");
                    setShowMentions(false);
                  }}
                  className="flex items-center gap-2 p-2 hover:bg-muted transition-colors text-left"
                >
                  <Avatar className="h-6 w-6">
                    <AvatarImage src={contact.profile_photo} className="object-cover" />
                    <AvatarFallback className="text-[8px]">{contact.name[0]}</AvatarFallback>
                  </Avatar>
                  <span className="text-xs font-medium">{contact.name}</span>
                </button>
              ))}
            </div>
          </ScrollArea>
        </div>
      )}
      
      <div className="flex gap-2 items-end">
        <div className="flex-1 relative">
          <Textarea 
            placeholder="Write a thoughtful comment... Use @ to mention someone." 
            className="min-h-[40px] max-h-32 py-3 pr-10 resize-none text-sm rounded-2xl shadow-inner bg-background border-muted focus:ring-1 focus:ring-primary"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <AtSign className="absolute right-3 top-2.5 h-4 w-4 text-muted-foreground opacity-50" />
        </div>
        <Button 
          size="icon" 
          className="h-10 w-10 rounded-xl shrink-0 shadow-md"
          disabled={!content.trim() || isSubmitting}
          onClick={handleAddComment}
        >
          {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}
