/**
 * Utility functions for the frontend
 */

/**
 * Gets the full URL for an image either from the API static folder or directly
 * from the URL if it's already a full URL
 */
export function getImageUrl(imagePath: string): string {
  if (!imagePath) return '';
  
  // If it's already a full URL, return it
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath;
  }
  
  // Otherwise, add the API static path
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  // Ensure path starts with /
  const path = imagePath.startsWith('/') ? imagePath : `/${imagePath}`;
  
  return `${apiUrl}${path}`;
}

/**
 * Formats a string to Title Case
 */
export function toTitleCase(str: string): string {
  return str
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Truncates a string to a specific length and adds ellipsis
 */
export function truncate(str: string, length: number): string {
  if (!str) return '';
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}
