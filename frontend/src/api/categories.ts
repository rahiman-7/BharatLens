import { apiClient } from './client';
import type { CategoriesResponse, StatesResponse, HealthResponse } from './types';

export async function getCategories(): Promise<CategoriesResponse> {
  return apiClient<CategoriesResponse>('/categories');
}

export async function getStates(): Promise<StatesResponse> {
  return apiClient<StatesResponse>('/states');
}

export async function getHealth(): Promise<HealthResponse> {
  return apiClient<HealthResponse>('/health');
}
