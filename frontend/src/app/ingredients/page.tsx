'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { API_URL } from '@/config';

// Custom hook for API fetching with better error handling
function useFetch<T>(url: string, options?: RequestInit) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(url, options);
      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
      
      const result = await response.json();
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Unknown error occurred'));
    } finally {
      setLoading(false);
    }
  }, [url, options]);

  return { data, error, loading, fetchData };
}

// Custom hook for persisting state to localStorage
function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  // Get from localStorage or use initialValue
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }
    
    try {
      const item = window.localStorage.getItem(key);
      // Parse stored json or return initialValue if none
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch (error) {
      return initialValue;
    }
  });
  
  // Return a wrapped version of useState's setter function that persists the new value to localStorage
  const setValue = useCallback((value: T) => {
    try {
      // Save state
      setStoredValue(value);
      
      // Save to localStorage
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(value));
      }
    } catch (error) {
      // Just handle the error silently
    }
  }, [key]);
  
  return [storedValue, setValue];
}

type Ingredient = {
  name: string;
  imageUrl: string;
  prompt: string;
};

// Component to handle image display with error handling
const IngredientImage = ({ imageUrl, name }: { imageUrl: string, name: string }) => {
  // Remove spaces from URL to prevent breaking Oracle Cloud PAR tokens
  const cleanedUrl = imageUrl.replace(/\s+/g, '');
  
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    // Check if this might be an Oracle Cloud URL with the wrong format
    const isOracleUrl = cleanedUrl.includes('objectstorage') && cleanedUrl.includes('oraclecloud.com');
    const hasPPath = cleanedUrl.includes('/p/');
    
    if (isOracleUrl && !hasPPath) {
      try {
        const url = new URL(cleanedUrl);
        const path = url.pathname;
        
        // Check if path contains namespace and bucket identifiers
        if (path.includes('/n/') && path.includes('/b/')) {
          // Extract namespace
          const nIndex = path.indexOf('/n/');
          const bIndex = path.indexOf('/b/');
          const namespace = path.substring(nIndex + 3, bIndex);
          
          // Extract bucket
          const oIndex = path.indexOf('/o/');
          let bucket = "";
          if (oIndex > bIndex) {
            bucket = path.substring(bIndex + 3, oIndex);
          } else {
            const afterB = path.substring(bIndex + 3);
            const nextSlash = afterB.indexOf('/');
            bucket = nextSlash > 0 ? afterB.substring(0, nextSlash) : afterB;
          }
          
          // Extract object name
          const parts = path.split('/');
          const objectName = parts[parts.length - 1];
          
          // Construct a proper Oracle URL
          const fixedUrl = `${url.protocol}//${url.host}/p/fixed-par-token/n/${namespace}/b/${bucket}/o/${objectName}`;
          
          // Try to load with fixed URL
          (e.target as HTMLImageElement).src = fixedUrl;
          return;
        }
      } catch (err) {
        // Silently handle errors
      }
    }
    
    // Try direct fetch as fallback
    fetch(cleanedUrl, { mode: 'no-cors' }).catch(() => {});
  };
  
  return (
    <img 
      src={cleanedUrl}
      alt={name}
      className="object-contain absolute inset-0 m-auto max-w-full max-h-full"
      crossOrigin="anonymous" 
      referrerPolicy="no-referrer"
      onError={handleImageError}
    />
  );
};

// Component for displaying ingredient cards
const IngredientCard = React.memo(({ ingredient }: { ingredient: Ingredient }) => {
  // Check if URL needs warning
  const needsWarning = ingredient.imageUrl && 
    /objectstorage.*oraclecloud\.com/.test(ingredient.imageUrl) && 
    !ingredient.imageUrl.includes('/p/');
  
  return (
    <div className="border rounded-lg p-4 shadow-md">
      <h2 className="text-xl font-semibold mb-2">{ingredient.name}</h2>
      
      <div className="relative h-40 bg-gray-100 rounded flex items-center justify-center mb-4">
        {!ingredient.imageUrl && (
          <div className="text-gray-400">No image available</div>
        )}
        
        {ingredient.imageUrl && (
          <div className="relative w-full h-full">
            <IngredientImage 
              imageUrl={ingredient.imageUrl} 
              name={ingredient.name} 
            />
          </div>
        )}
      </div>
      
      {needsWarning && (
        <div className="flex flex-wrap gap-2">
          <span className="bg-yellow-100 text-yellow-800 py-1 px-3 rounded text-sm">
            ⚠️ Oracle URL may need reformatting
          </span>
        </div>
      )}
    </div>
  );
});

export default function IngredientsPage() {
  // Basic states
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [loading, setLoading] = useState(true);
  const [dbPopulated, setDbPopulated] = useState(false);
  
  // Default prompt template (for fallback ingredients)
  const defaultPromptTemplate = '2D flat icon of cooking {ingredient}, emoji style, minimal cartoon vector art, transparent background';
  
  // Persistent state with localStorage
  const [searchQuery, setSearchQuery] = useLocalStorage('ingredientsSearchQuery', '');
  const [currentPage, setCurrentPage] = useLocalStorage('ingredientsCurrentPage', 1);
  
  // Other states
  const [totalIngredients, setTotalIngredients] = useState(0);
  const itemsPerPage = 50; // Show 50 ingredients per page
  
  // Function to check if database is populated with ingredients
  const checkDatabase = async () => {
    try {
      const response = await fetch(`${API_URL}/ingredients?limit=1`);
      const responseData = await response.json();
      
      // Extract the data from the nested structure
      const data = responseData.data || responseData;
      
      console.log("Check DB response:", data);
      
      if (data.total > 0) {
        setDbPopulated(true);
        if (data.total !== totalIngredients) {
          setTotalIngredients(data.total);
        }
      } else {
        setDbPopulated(false);
        setTotalIngredients(0);
      }
      
      setLoading(false);
    } catch (error) {
      console.error("Error checking database:", error);
      setLoading(false);
    }
  };
  
  // Fetch ingredients from the database with pagination
  const fetchPagedIngredients = async (page: number) => {
    try {
      setLoading(true);
      const offset = (page - 1) * itemsPerPage;
      
      // Build URL with search parameter if one exists
      let url = `${API_URL}/ingredients?limit=${itemsPerPage}&offset=${offset}`;
      if (searchQuery) {
        url += `&search=${encodeURIComponent(searchQuery)}`;
      }
      
      console.log("Fetching ingredients with URL:", url);
      const response = await fetch(url);
      const responseData = await response.json();
      
      // Extract the data from the nested structure
      const data = responseData.data || responseData;
      
      console.log("Fetch ingredients response:", data);
      
      // Update total count if available
      if (data.total !== undefined) {
        setTotalIngredients(data.total);
      }
      
      // Check if ingredients array exists
      if (!data.ingredients || !Array.isArray(data.ingredients)) {
        console.error("Invalid ingredients data format:", data);
        setIngredients([]);
        setLoading(false);
        return;
      }
      
      // Map the data to our expected format
      const formattedIngredients = data.ingredients.map((item: any) => ({
        id: item.id,
        name: item.name,
        imageUrl: item.url || '',
        prompt: item.prompt || defaultPromptTemplate.replace('{ingredient}', item.name)
      }));
      
      console.log("Formatted ingredients:", formattedIngredients);
      
      setIngredients(formattedIngredients);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching ingredients:", error);
      setLoading(false);
    }
  };
  
  // Initial data loading
  useEffect(() => {
    // Try to load from database first
    const initData = async () => {
      try {
        await checkDatabase();
      } catch (error) {
        console.error("Error in initial data loading:", error);
      }
    };
    
    initData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  // Fetch ingredients whenever the page changes, search query changes, or database is populated
  useEffect(() => {
    if (dbPopulated) {
      // Reset to page 1 when search query changes
      if (searchQuery !== '') {
        setCurrentPage(1);
      }
      fetchPagedIngredients(currentPage);
    }
  }, [currentPage, searchQuery, dbPopulated, itemsPerPage]);
  
  // Handle search submit
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Search is already handled by the useEffect, but we need this to handle form submission
    fetchPagedIngredients(1);
    setCurrentPage(1);
  };
  
  // Fetch total count periodically
  useEffect(() => {
    if (!dbPopulated) return; // Skip if db not populated
    
    const fetchTotalCount = () => {
      fetch(`${API_URL}/ingredients?limit=1`)
        .then(response => response.json())
        .then(responseData => {
          // Handle nested response structure
          const data = responseData.data || responseData;
          console.log("Periodic check response:", data);
          
          if (data.total > 0 && data.total !== totalIngredients) {
            setTotalIngredients(data.total);
          }
        })
        .catch((error) => {
          console.error("Error in periodic check:", error);
        });
    };
    
    // Run immediately on component mount if db is populated
    fetchTotalCount();
    
    // Set interval for periodic updates - using a longer interval of 30 seconds
    const intervalId = setInterval(fetchTotalCount, 30000);
    return () => clearInterval(intervalId);
  }, [dbPopulated, totalIngredients]);
  
  
  // We'll rely on backend filtering for search instead of client-side filtering
  const filteredIngredients = ingredients;
  
  // Calculate pagination values
  const totalPages = Math.ceil(totalIngredients / itemsPerPage);
  
  // Generate page numbers to display with a sliding window approach
  const getPageNumbers = () => {
    const maxPageDisplay = 5; // Show at most 5 page numbers at a time
    
    if (totalPages <= maxPageDisplay) {
      // Show all pages if there are 5 or fewer
      return Array.from({length: totalPages}, (_, i) => i + 1);
    }
    
    // Complex pagination logic for many pages
    if (currentPage <= 3) {
      // Near the start
      return Array.from({length: 5}, (_, i) => i + 1);
    } else if (currentPage >= totalPages - 2) {
      // Near the end
      return Array.from({length: 5}, (_, i) => totalPages - 4 + i);
    } else {
      // In the middle
      return Array.from({length: 5}, (_, i) => currentPage - 2 + i);
    }
  };
  
  // Create a Pagination component to avoid duplication
  const Pagination = () => (
    <nav className="inline-flex rounded-md shadow">
      <button
        onClick={() => changePage(1)}
        disabled={currentPage === 1}
        className={`px-3 py-1 rounded-l-md border ${
          currentPage === 1 
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
            : 'bg-white text-blue-500 hover:bg-blue-50'
        }`}
      >
        &laquo; First
      </button>
      
      <button
        onClick={() => changePage(currentPage - 1)}
        disabled={currentPage === 1}
        className={`px-3 py-1 border-t border-b ${
          currentPage === 1 
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
            : 'bg-white text-blue-500 hover:bg-blue-50'
        }`}
      >
        &lt; Prev
      </button>
      
      {getPageNumbers().map(page => (
        <button
          key={page}
          onClick={() => changePage(page)}
          className={`px-3 py-1 border-t border-b ${
            currentPage === page
              ? 'bg-blue-500 text-white'
              : 'bg-white text-blue-500 hover:bg-blue-50'
          }`}
        >
          {page}
        </button>
      ))}
      
      <button
        onClick={() => changePage(currentPage + 1)}
        disabled={currentPage === totalPages}
        className={`px-3 py-1 border-t border-b ${
          currentPage === totalPages
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-white text-blue-500 hover:bg-blue-50'
        }`}
      >
        Next &gt;
      </button>
      
      <button
        onClick={() => changePage(totalPages)}
        disabled={currentPage === totalPages}
        className={`px-3 py-1 rounded-r-md border ${
          currentPage === totalPages
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-white text-blue-500 hover:bg-blue-50'
        }`}
      >
        Last &raquo;
      </button>
    </nav>
  );
  
  // Handle page change
  const changePage = (page: number) => {
    setCurrentPage(page);
    // Scroll to top when changing pages
    window.scrollTo(0, 0);
  };
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-4">Ingredient Library</h1>
      
      {/* Search and filters */}
      <form onSubmit={handleSearchSubmit} className="mb-6 flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
            Search ingredients
          </label>
          <div className="flex">
            <input
              type="text"
              id="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name..."
              className="w-full p-2 border border-gray-300 rounded-l"
            />
            <button 
              type="submit"
              className="bg-primary-500 text-white px-4 py-2 rounded-r hover:bg-primary-600"
            >
              Search
            </button>
          </div>
        </div>
        
      </form>
      
      <p className="text-gray-600 mb-8">
        Showing {filteredIngredients.length} of {totalIngredients} ingredients (Page {currentPage} of {totalPages})
      </p>
      
      
      {/* Pagination Controls (Top) */}
      {totalPages > 1 && (
        <div className="flex justify-center mb-8">
          <Pagination />
        </div>
      )}
      
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="text-blue-500 flex flex-col items-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-500 mb-4"></div>
            <span className="text-xl">Loading ingredients...</span>
          </div>
        </div>
      ) : filteredIngredients.length === 0 ? (
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500 flex flex-col items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-xl">No ingredients match your filters</span>
            <button 
              onClick={() => setSearchQuery('')}
              className="mt-4 bg-blue-500 hover:bg-blue-700 text-white py-2 px-4 rounded"
            >
              Clear Filters
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredIngredients.map((ingredient) => (
            <IngredientCard 
              key={ingredient.name} 
              ingredient={ingredient} 
            />
          ))}
        </div>
      )}
      
      {/* Pagination Controls (Bottom) */}
      {totalPages > 1 && (
        <div className="flex justify-center mt-8">
          <Pagination />
        </div>
      )}
      
    </div>
  );
}
