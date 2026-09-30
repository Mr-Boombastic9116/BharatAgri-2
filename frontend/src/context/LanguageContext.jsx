import React, { createContext, useContext, useState, useEffect } from 'react';
import en from '../locales/en.json';
import hi from '../locales/hi.json';
import mr from '../locales/mr.json';

const translations = { en, hi, mr };

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => {
    return localStorage.getItem('bharatagri_lang') || 'en';
  });

  useEffect(() => {
    localStorage.setItem('bharatagri_lang', lang);
  }, [lang]);

  const t = (key) => {
    if (translations[lang] && translations[lang][key]) {
      return translations[lang][key];
    }
    // Fallback to English
    return (translations.en && translations.en[key]) || key;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useTranslation() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useTranslation must be used within a LanguageProvider');
  }
  return context;
}
