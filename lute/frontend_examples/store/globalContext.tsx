import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: number;
  name: string;
  email: string;
}

interface UserSettings {
  theme: 'light' | 'dark';
  language: string;
  itemsPerPage: number;
}

interface GlobalContextType {
  user: User | null;
  settings: UserSettings;
  setUser: (user: User | null) => void;
  updateSettings: (settings: Partial<UserSettings>) => void;
  isLoading: boolean;
}

const GlobalContext = createContext<GlobalContextType | undefined>(undefined);

export const GlobalContextProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [settings, setSettings] = useState<UserSettings>({
    theme: 'light',
    language: 'en',
    itemsPerPage: 25,
  });
  const [isLoading, setIsLoading] = useState(true);

  // Initialize from localStorage and fetch user data
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Load settings from localStorage
        const savedSettings = localStorage.getItem('userSettings');
        if (savedSettings) {
          setSettings(JSON.parse(savedSettings));
        }

        // Fetch current user
        const response = await fetch('/api/user');
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        }
      } catch (error) {
        console.error('Failed to initialize app:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeApp();
  }, []);

  const updateSettings = (newSettings: Partial<UserSettings>) => {
    const updated = { ...settings, ...newSettings };
    setSettings(updated);
    localStorage.setItem('userSettings', JSON.stringify(updated));
  };

  return (
    <GlobalContext.Provider
      value={{
        user,
        settings,
        setUser,
        updateSettings,
        isLoading,
      }}
    >
      {children}
    </GlobalContext.Provider>
  );
};

export const useGlobalContext = () => {
  const context = useContext(GlobalContext);
  if (!context) {
    throw new Error('useGlobalContext must be used within GlobalContextProvider');
  }
  return context;
};
