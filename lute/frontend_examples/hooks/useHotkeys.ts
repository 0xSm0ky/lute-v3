import { useEffect, useCallback, useState } from 'react';
import type { RefObject } from 'react';

export const useHotkeys = (
  bindings: Record<string, () => void>,
  options?: {
    disabled?: boolean;
    preventDefault?: boolean;
  }
) => {
  const handleKeyPress = useCallback(
    (event: KeyboardEvent) => {
      if (options?.disabled) return;

      for (const [key, handler] of Object.entries(bindings)) {
        const keyMatch = event.key.toLowerCase() === key.toLowerCase();
        const ctrlMatch = !key.includes('ctrl') || event.ctrlKey || event.metaKey;
        const shiftMatch = !key.includes('shift') || event.shiftKey;
        const altMatch = !key.includes('alt') || event.altKey;

        if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
          if (options?.preventDefault) {
            event.preventDefault();
          }
          handler();
          break;
        }
      }
    },
    [bindings, options]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [handleKeyPress]);
};

// Hook for tracking focus
export const useClickOutside = (
  ref: RefObject<HTMLElement>,
  callback: () => void
) => {
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [ref, callback]);
};

// Hook for debouncing
export const useDebounce = <T,>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};
