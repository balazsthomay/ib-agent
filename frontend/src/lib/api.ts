/**
 * API client for backend communication
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Project {
  id: string
  name: string
  description?: string
  target_company?: string
  status: 'draft' | 'active' | 'completed' | 'archived'
  firm_id: string
  created_at: string
  updated_at: string
}

export interface CreateProjectRequest {
  name: string
  description?: string
  target_company?: string
}

/**
 * Get authentication token from Clerk
 */
async function getAuthToken(): Promise<string> {
  // Token will be available via Clerk's auth() in Server Components
  // or via useAuth() hook in Client Components
  throw new Error('getAuthToken must be called from authenticated context')
}

/**
 * Fetch all projects for the current user's firm
 */
export async function getProjects(token: string): Promise<Project[]> {
  const response = await fetch(`${API_URL}/api/projects`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch projects: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Create a new project
 */
export async function createProject(
  token: string,
  data: CreateProjectRequest
): Promise<Project> {
  const response = await fetch(`${API_URL}/api/projects`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to create project')
  }

  return response.json()
}

/**
 * Get a single project by ID
 */
export async function getProject(token: string, id: string): Promise<Project> {
  const response = await fetch(`${API_URL}/api/projects/${id}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch project: ${response.statusText}`)
  }

  return response.json()
}
