import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format text to improve readability by adding spaces between words
 * that might be incorrectly concatenated.
 */
export function formatReadableText(text: string): string {
  if (!text) return '';
  
  // First, add spaces between camelCase or PascalCase words
  let result = text.replace(/([a-z])([A-Z])/g, '$1 $2');
  
  // Add spaces after commas without spaces
  result = result.replace(/,(?=[^\s])/g, ', ');
  
  // Add spaces after periods followed by uppercase letters (sentence boundaries)
  result = result.replace(/\.([A-Z])/g, '. $1');
  
  // Add spaces after question marks followed by uppercase letters
  result = result.replace(/\?([A-Z])/g, '? $1');
  
  // Add spaces after exclamation marks followed by uppercase letters
  result = result.replace(/\!([A-Z])/g, '! $1');
  
  // Add spaces after semicolons followed by uppercase letters
  result = result.replace(/\;([A-Z])/g, '; $1');
  
  // Add zero-width spaces in very long words to allow better line breaking
  result = result.replace(/(\S{20})(?=\S)/g, '$1\u200B');
  
  return result;
}
