import enChat from '../dictionaries/en/chat.json';
import enHome from '../dictionaries/en/home.json';
import enSettings from '../dictionaries/en/settings.json';
import enLayout from '../dictionaries/en/layout.json';
import zhChat from '../dictionaries/zh/chat.json';
import zhHome from '../dictionaries/zh/home.json';
import zhSettings from '../dictionaries/zh/settings.json';
import zhLayout from '../dictionaries/zh/layout.json';

// Define the supported languages
export const languages = ['en', 'zh'];
export const defaultLanguage = 'en';

// Dictionary type definition
interface Dictionaries {
  chat: any;
  home: any;
  settings: any;
  layout: any;
}

// Dictionary collections by language
const dictionaries: Record<string, Dictionaries> = {
  en: {
    chat: enChat,
    home: enHome,
    settings: enSettings,
    layout: enLayout
  },
  zh: {
    chat: zhChat,
    home: zhHome,
    settings: zhSettings,
    layout: zhLayout
  }
};

export function getDictionary(locale: string): Dictionaries {
  // If the requested locale isn't supported, use the default
  if (!languages.includes(locale)) {
    return dictionaries[defaultLanguage];
  }
  
  return dictionaries[locale];
} 