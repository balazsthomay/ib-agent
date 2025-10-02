'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@clerk/nextjs'
import { createProject } from '@/lib/api'

export function CreateProjectButton() {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()
  const { getToken } = useAuth()

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    const formData = new FormData(e.currentTarget)
    const data = {
      name: formData.get('name') as string,
      description: formData.get('description') as string || undefined,
      target_company: formData.get('target_company') as string || undefined,
    }

    try {
      const token = await getToken()
      if (!token) {
        throw new Error('Not authenticated')
      }

      const project = await createProject(token, data)
      setIsOpen(false)
      router.refresh()
      router.push(`/projects/${project.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create project')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="px-4 py-2 rounded-md bg-foreground text-background hover:bg-foreground/90 font-medium"
      >
        New Project
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background rounded-lg p-6 w-full max-w-md border border-border">
            <h2 className="text-2xl font-bold mb-4">Create New Project</h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium mb-1">
                  Project Name *
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  required
                  className="w-full px-3 py-2 rounded-md border border-border bg-background focus:outline-none focus:ring-2 focus:ring-foreground/20"
                  placeholder="Q4 2025 M&A Targets"
                />
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium mb-1">
                  Description
                </label>
                <textarea
                  id="description"
                  name="description"
                  rows={3}
                  className="w-full px-3 py-2 rounded-md border border-border bg-background focus:outline-none focus:ring-2 focus:ring-foreground/20"
                  placeholder="Identify acquisition targets in the tech sector..."
                />
              </div>

              <div>
                <label htmlFor="target_company" className="block text-sm font-medium mb-1">
                  Target Company
                </label>
                <input
                  id="target_company"
                  name="target_company"
                  type="text"
                  className="w-full px-3 py-2 rounded-md border border-border bg-background focus:outline-none focus:ring-2 focus:ring-foreground/20"
                  placeholder="Acme Corp"
                />
              </div>

              {error && (
                <div className="bg-destructive/10 text-destructive px-3 py-2 rounded-md text-sm">
                  {error}
                </div>
              )}

              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  disabled={isLoading}
                  className="px-4 py-2 rounded-md border border-border hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-4 py-2 rounded-md bg-foreground text-background hover:bg-foreground/90 disabled:opacity-50"
                >
                  {isLoading ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
