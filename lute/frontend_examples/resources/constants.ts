// Hotkeys
export const HOTKEYS = {
  NEXT_TERM: 'n',
  PREV_TERM: 'p',
  NEXT_PAGE: 'ArrowRight',
  PREV_PAGE: 'ArrowLeft',
  PLAY_AUDIO: 'a',
  EDIT_TERM: 'e',
  SHOW_DEFINITION: 'd',
  MARK_KNOWN: 'm',
  MARK_LEARNING: 'l',
  MARK_UNKNOWN: 'u',
} as const;

// Term statuses
export const TERM_STATUSES = {
  NEW: 0,
  LEARNING: 1,
  KNOWN: 2,
  IGNORED: 3,
  WELL_KNOWN: 4,
  ARCHIVED: 5,
} as const;

export const TERM_STATUS_LABELS = {
  0: 'New',
  1: 'Learning',
  2: 'Known',
  3: 'Ignored',
  4: 'Well Known',
  5: 'Archived',
} as const;

// Pagination
export const DEFAULT_PAGE_SIZE = 25;
export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

// API endpoints
export const API_ENDPOINTS = {
  BOOKS: '/api/books',
  LANGUAGES: '/api/languages',
  TERMS: '/api/terms',
  USER: '/api/user',
  SETTINGS: '/api/settings',
  STATS: '/api/stats',
} as const;

// Table configuration
export const TABLE_COLUMN_SIZES = {
  SMALL: 100,
  MEDIUM: 200,
  LARGE: 300,
} as const;
