// User
export interface User {
  id: number;
  username: string;
  email: string;
}

// Book
export interface Book {
  id: number;
  title: string;
  languageId: number;
  languageName: string;
  pageCount: number;
  readTermCount: number;
  createdAt: string;
}

// Term
export interface Term {
  id: number;
  text: string;
  definition: string;
  status: 0 | 1 | 2 | 3 | 4 | 5;
  bookId: number;
  createdAt: string;
}

// Language
export interface Language {
  id: number;
  name: string;
  isoCode: string;
  active: boolean;
}

// Page
export interface Page {
  id: number;
  bookId: number;
  pageNumber: number;
  content: string;
}

// Settings
export interface UserSettings {
  theme: 'light' | 'dark';
  language: string;
  itemsPerPage: number;
}

// API Response wrapper
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
