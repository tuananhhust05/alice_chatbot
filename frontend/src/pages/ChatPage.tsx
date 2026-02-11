import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import ChatArea from '../components/ChatArea';
import SpaceBackground from '../components/SpaceBackground';
import { Conversation, ConversationDetail, Message } from '../types';
import { getConversations, getConversation, deleteConversation } from '../api/chat';
import { HiOutlineBars3 } from 'react-icons/hi2';

const ChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<ConversationDetail | null>(null);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false); // Default closed on mobile
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [isMobile, setIsMobile] = useState(false);

  // Detect screen size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
      // Open sidebar by default on desktop
      if (window.innerWidth >= 1024) {
        setSidebarOpen(true);
      }
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const fetchConversations = useCallback(async () => {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setLoadingConversations(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const handleSelectConversation = useCallback(async (id: string) => {
    setActiveConversationId(id);
    try {
      const detail = await getConversation(id);
      setActiveConversation(detail);
      // Close sidebar on mobile after selection
      if (isMobile) {
        setSidebarOpen(false);
      }
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  }, [isMobile]);

  const handleNewChat = useCallback(() => {
    setActiveConversationId(null);
    setActiveConversation(null);
    // Close sidebar on mobile
    if (isMobile) {
      setSidebarOpen(false);
    }
  }, [isMobile]);

  const handleDeleteConversation = useCallback(async (id: string) => {
    try {
      await deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (activeConversationId === id) {
        setActiveConversationId(null);
        setActiveConversation(null);
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  }, [activeConversationId]);

  const handleConversationUpdate = useCallback((
    conversationId: string,
    newMessage: Message,
    title?: string,
  ) => {
    // Update active conversation
    setActiveConversationId(conversationId);
    setActiveConversation(prev => {
      if (prev && prev.id === conversationId) {
        return {
          ...prev,
          messages: [...prev.messages, newMessage],
          title: title || prev.title,
        };
      }
      return prev;
    });

    // Refresh conversation list
    fetchConversations();
  }, [fetchConversations]);

  const handleNewConversationCreated = useCallback((
    conversationId: string,
    messages: Message[],
    title?: string,
  ) => {
    setActiveConversationId(conversationId);
    setActiveConversation({
      id: conversationId,
      title: title || 'New Conversation',
      messages,
      file_ids: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
    fetchConversations();
  }, [fetchConversations]);

  return (
    <div className="h-screen h-[100dvh] w-screen flex bg-black overflow-hidden relative">
      {/* 3D Space Background */}
      <SpaceBackground />
      
      {/* Mobile menu button - fixed position, hide when sidebar is open */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="lg:hidden fixed top-3 left-3 z-50 w-10 h-10 flex items-center justify-center rounded-xl bg-apple-surface/90 backdrop-blur-lg glass-border text-white hover:bg-apple-elevated transition-colors shadow-lg"
          aria-label="Open menu"
        >
          <HiOutlineBars3 className="w-5 h-5" />
        </button>
      )}

      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        loading={loadingConversations}
      />

      {/* Chat Area */}
      <ChatArea
        conversation={activeConversation}
        conversationId={activeConversationId}
        onConversationUpdate={handleConversationUpdate}
        onNewConversationCreated={handleNewConversationCreated}
      />
    </div>
  );
};

export default ChatPage;
