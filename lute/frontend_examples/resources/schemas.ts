import { z } from 'zod';

// Book schemas
export const bookCreateSchema = z.object({
  title: z.string().min(1, 'Title is required').max(255, 'Title must be less than 255 characters'),
  languageId: z.number().min(1, 'Language is required'),
});

export const bookUpdateSchema = bookCreateSchema.partial();

// Term schemas
export const termCreateSchema = z.object({
  text: z.string().min(1, 'Term text is required'),
  definition: z.string().optional(),
  bookId: z.number().min(1, 'Book is required'),
  status: z.number().min(0).max(5).optional(),
});

export const termUpdateSchema = termCreateSchema.partial();

// Language schemas
export const languageSchema = z.object({
  name: z.string().min(1, 'Language name is required'),
  isoCode: z.string().length(2, 'ISO code must be 2 characters'),
});

// Settings schemas
export const settingsSchema = z.object({
  theme: z.enum(['light', 'dark']),
  language: z.string(),
  itemsPerPage: z.number().min(5).max(100),
});

// Export types
export type BookCreateInput = z.infer<typeof bookCreateSchema>;
export type BookUpdateInput = z.infer<typeof bookUpdateSchema>;
export type TermCreateInput = z.infer<typeof termCreateSchema>;
export type TermUpdateInput = z.infer<typeof termUpdateSchema>;
export type LanguageInput = z.infer<typeof languageSchema>;
export type SettingsInput = z.infer<typeof settingsSchema>;
