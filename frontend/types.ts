/**
 * Type definitions for the Sizzle application
 */

export interface Ingredient {
  id?: number;
  name: string;
  quantity?: string;
  url?: string;
}

export interface Equipment {
  id?: number;
  name: string;
  url?: string;
}

export interface RecipeStep {
  id?: number;
  instruction: string;
  action?: string;
  action_image?: string;
  step_image?: string;
  ingredients: Ingredient[];
  equipment: Equipment[];
}

export interface Recipe {
  id?: number;
  title: string;
  description: string;
  prepTime?: string;
  prep_time?: string;
  cookTime?: string;
  cook_time?: string;
  servings: number;
  ingredients: Ingredient[];
  equipment: Equipment[];
  steps: RecipeStep[];
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  message?: string;
}
