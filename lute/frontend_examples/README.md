# Frontend Examples for Lute v3 Migration

This directory contains example files and patterns extracted from the `oashrafov/lute-v3-frontend` repository. These serve as a reference for modernizing the Lute v3 frontend.

## Directory Structure

- **store/** - State management with React Context
- **hooks/** - Custom React hooks for common operations
- **resources/** - Constants, types, and schemas
- **components/** - Example components (coming soon)
- **features/** - Feature module examples (coming soon)

## Key Patterns

### 1. Global State Management
See `store/globalContext.tsx` for a clean pattern using React Context.

### 2. Data Fetching with TanStack Query
See `hooks/useBook.ts` for examples of:
- Fetching data with automatic caching
- Creating, updating, and deleting resources
- Automatic query invalidation on mutations

### 3. Type Safety with Zod
See `resources/schemas.ts` for runtime validation and TypeScript type generation.

### 4. Type Definitions
See `resources/types.ts` for all API and internal type definitions.

### 5. Custom Hooks
See `hooks/useHotkeys.ts` for reusable hook patterns:
- Keyboard event handling
- Click outside detection
- Debouncing

## Installation

To use these patterns in the main application:

1. Install required dependencies:
```bash
npm install react-query @tanstack/react-query zod react-hook-form @hookform/resolvers
```

2. Copy files to your frontend directory
3. Adapt paths and imports as needed

## Next Steps

1. Review `FRONTEND_IMPROVEMENTS.md` for the complete migration strategy
2. Examine the `oashrafov/lute-v3-frontend` repository for more examples
3. Start with Phase 1 of the migration strategy
4. Gradually adopt these patterns in new features

## References

- TanStack Query: https://tanstack.com/query/latest
- React Hook Form: https://react-hook-form.com/
- Zod: https://zod.dev/
- Mantine UI: https://mantine.dev/
- TanStack Router: https://tanstack.com/router/latest
