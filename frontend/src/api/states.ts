import { apiClient } from './client';
import type { StatesMetadataResponse, ApiStateMetadata } from './types';

export async function getStatesMetadata(): Promise<StatesMetadataResponse> {
  const data = await apiClient<any>('/states');
  if (Array.isArray(data)) {
    return { total: data.length, states: data };
  }
  return data;
}

export async function getStateBySlug(slug: string): Promise<ApiStateMetadata> {
  return apiClient<ApiStateMetadata>(`/states/${encodeURIComponent(slug)}`);
}

