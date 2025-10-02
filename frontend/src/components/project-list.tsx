'use client'

import { Project } from '@/lib/api'
import Link from 'next/link'

interface ProjectListProps {
  projects: Project[]
}

export function ProjectList({ projects }: ProjectListProps) {
  if (projects.length === 0) {
    return (
      <div className="text-center py-12 bg-muted/50 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">No projects yet</h3>
        <p className="text-muted-foreground mb-4">
          Get started by creating your first project
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {projects.map((project) => (
        <Link
          key={project.id}
          href={`/projects/${project.id}`}
          className="block p-6 rounded-lg border border-border hover:border-foreground/20 transition-colors"
        >
          <div className="flex items-start justify-between mb-3">
            <h3 className="font-semibold text-lg">{project.name}</h3>
            <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(project.status)}`}>
              {project.status}
            </span>
          </div>

          {project.description && (
            <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
              {project.description}
            </p>
          )}

          {project.target_company && (
            <p className="text-sm text-foreground/60">
              <span className="font-medium">Target:</span> {project.target_company}
            </p>
          )}

          <p className="text-xs text-muted-foreground mt-3">
            Created {new Date(project.created_at).toLocaleDateString()}
          </p>
        </Link>
      ))}
    </div>
  )
}

function getStatusColor(status: Project['status']): string {
  switch (status) {
    case 'draft':
      return 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
    case 'active':
      return 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
    case 'completed':
      return 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
    case 'archived':
      return 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400'
    default:
      return 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
  }
}
