import React, { useState } from 'react';
import { Conversation } from '../types';
import { useAuth } from '../context/AuthContext';
import { format, isToday, isYesterday, isThisWeek } from 'date-fns';
import {
  HiOutlinePlusCircle,
  HiOutlineChatBubbleLeftRight,
  HiOutlineTrash,
  HiOutlineArrowRightOnRectangle,
  HiSparkles,
  HiOutlineXMark,
} from 'react-icons/hi2';

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onDeleteConversation: (id: string) => void;
  isOpen: boolean;
  onClose: () => void;
  loading: boolean;
}

const groupConversations = (conversations: Conversation[]) => {
  const groups: { label: string; items: Conversation[] }[] = [];
  const today: Conversation[] = [];
  const yesterday: Conversation[] = [];
  const thisWeek: Conversation[] = [];
  const older: Conversation[] = [];

  conversations.forEach(conv => {
    const date = new Date(conv.updated_at);
    if (isToday(date)) today.push(conv);
    else if (isYesterday(date)) yesterday.push(conv);
    else if (isThisWeek(date)) thisWeek.push(conv);
    else older.push(conv);
  });

  if (today.length) groups.push({ label: 'Today', items: today });
  if (yesterday.length) groups.push({ label: 'Yesterday', items: yesterday });
  if (thisWeek.length) groups.push({ label: 'This Week', items: thisWeek });
  if (older.length) groups.push({ label: 'Older', items: older });

  return groups;
};

const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  isOpen,
  onClose,
  loading,
}) => {
  const { user, logout } = useAuth();
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const groups = groupConversations(conversations);

  return (
    <>
      {/* Overlay for mobile/tablet */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 z-30 backdrop-blur-sm"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed lg:relative z-40 h-full
          w-[280px] sm:w-[300px] lg:w-72 flex flex-col
          bg-apple-surface/95 backdrop-blur-xl
          border-r border-apple-border
          transition-transform duration-300 ease-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          safe-area-inset
        `}
      >
        {/* Header */}
        <div className="p-4 pt-5 lg:pt-4 flex items-center justify-between border-b border-apple-border">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#0A84FF] to-[#5E5CE6] flex items-center justify-center">
              <HiSparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-[15px] text-white">Alice</span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={onNewChat}
              className="w-8 h-8 flex items-center justify-center rounded-lg text-apple-secondary hover:text-white hover:bg-apple-elevated transition-all"
              title="New Chat"
            >
              <HiOutlinePlusCircle className="w-5 h-5" />
            </button>
            {/* Close button for mobile */}
            <button
              onClick={onClose}
              className="lg:hidden w-8 h-8 flex items-center justify-center rounded-lg text-apple-secondary hover:text-white hover:bg-apple-elevated transition-all"
            >
              <HiOutlineXMark className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* New Chat button */}
        <div className="px-3 pt-3">
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-apple-accent hover:bg-apple-elevated/60 transition-all group"
          >
            <HiOutlinePlusCircle className="w-5 h-5 group-hover:scale-110 transition-transform" />
            New Conversation
          </button>
        </div>

        {/* Conversations list */}
        <div className="flex-1 overflow-y-auto px-3 py-2">
          {loading ? (
            <div className="flex flex-col gap-2 mt-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-10 rounded-xl bg-apple-elevated/50 animate-pulse" />
              ))}
            </div>
          ) : conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-apple-tertiary text-sm">
              <HiOutlineChatBubbleLeftRight className="w-8 h-8 mb-2 opacity-50" />
              <p>No conversations yet</p>
            </div>
          ) : (
            groups.map(group => (
              <div key={group.label} className="mb-3">
                <p className="text-[11px] font-medium text-apple-tertiary uppercase tracking-wider px-3 py-2">
                  {group.label}
                </p>
                {group.items.map(conv => (
                  <div
                    key={conv.id}
                    className={`
                      group relative flex items-center gap-2.5 px-3 py-2 rounded-xl cursor-pointer
                      transition-all duration-150 mb-0.5
                      ${activeConversationId === conv.id
                        ? 'bg-apple-elevated text-white'
                        : 'text-apple-secondary hover:bg-apple-elevated/40 hover:text-white'
                      }
                    `}
                    onClick={() => onSelectConversation(conv.id)}
                    onMouseEnter={() => setHoveredId(conv.id)}
                    onMouseLeave={() => setHoveredId(null)}
                  >
                    <HiOutlineChatBubbleLeftRight className="w-4 h-4 flex-shrink-0 opacity-60" />
                    <span className="text-sm truncate flex-1">{conv.title}</span>
                    {hoveredId === conv.id && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteConversation(conv.id);
                        }}
                        className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-md text-apple-tertiary hover:text-apple-red hover:bg-apple-red/10 transition-all"
                        title="Delete"
                      >
                        <HiOutlineTrash className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ))
          )}
        </div>

        {/* User section */}
        <div className="p-3 border-t border-apple-border">
          <div className="flex items-center gap-3 px-3 py-2 rounded-xl">
            {user?.picture ? (
              <img
                src={user.picture}
                alt={user.name}
                className="w-8 h-8 rounded-full ring-1 ring-apple-border"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-apple-elevated flex items-center justify-center text-sm font-medium">
                {user?.name?.[0] || '?'}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.name}</p>
              <p className="text-[11px] text-apple-tertiary truncate">{user?.email}</p>
            </div>
            <button
              onClick={logout}
              className="w-8 h-8 flex items-center justify-center rounded-lg text-apple-tertiary hover:text-apple-red hover:bg-apple-red/10 transition-all"
              title="Sign Out"
            >
              <HiOutlineArrowRightOnRectangle className="w-4.5 h-4.5" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
