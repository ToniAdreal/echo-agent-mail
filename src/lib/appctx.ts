import { createContext, useContext } from 'react';
import type { Me } from './api';

export interface ComposerOpts {
  mode?: 'new' | 'reply' | 'reply_all' | 'forward';
  messageId?: string;
  draftId?: string;
  initial?: { to?: string; subject?: string; body?: string };
  onDone?: () => void;
}

export interface AppState {
  me: Me;
  theme: 'day' | 'night';
  setTheme: (t: 'day' | 'night', persist?: boolean) => void;
  badges: { review: number; tasks: number; decisions: number; inbox_unread: number };
  refreshBadges: () => void;
  environment: 'demo' | 'live';
  agentAvailable: boolean;
  openComposer: (opts?: ComposerOpts) => void;
  logout: () => void;
}

export const AppCtx = createContext<AppState>(null as unknown as AppState);
export const useApp = () => useContext(AppCtx);
