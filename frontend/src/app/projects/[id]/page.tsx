import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { getProject } from '@/lib/api'
import { UserButton } from '@clerk/nextjs'
import Link from 'next/link'

interface ProjectPageProps {
  params: Promise<{
    id: string
  }>
}

export default async function ProjectPage({ params }: ProjectPageProps) {
  const { getToken, userId } = await auth()

  if (!userId) {
    redirect('/')
  }

  const token = await getToken()
  if (!token) {
    redirect('/')
  }

  const { id } = await params
  let project = null
  let error = null

  try {
    project = await getProject(token, id)
  } catch (e) {
    error = e instanceof Error ? e.message : 'Failed to load project'
    console.error('Error loading project:', e)
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b border-border">
          <div className="container mx-auto px-4 py-4 flex justify-between items-center">
            <Link href="/" className="text-2xl font-bold">
              IB Agent
            </Link>
            <div className="flex gap-4 items-center">
              <Link href="/dashboard" className="px-4 py-2 text-sm font-medium">
                Dashboard
              </Link>
              <UserButton />
            </div>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8">
          <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-lg">
            {error || 'Project not found'}
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold">
            IB Agent
          </Link>
          <div className="flex gap-4 items-center">
            <Link href="/dashboard" className="px-4 py-2 text-sm font-medium">
              Dashboard
            </Link>
            <UserButton />
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Link
            href="/dashboard"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← Back to Projects
          </Link>
        </div>

        <div className="mb-8">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold mb-2">{project.name}</h1>
              {project.description && (
                <p className="text-muted-foreground">{project.description}</p>
              )}
            </div>
            <span className={`text-sm px-3 py-1 rounded-full ${getStatusColor(project.status)}`}>
              {project.status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 p-4 bg-muted/50 rounded-lg">
            {project.target_company && (
              <div>
                <p className="text-sm text-muted-foreground">Target Company</p>
                <p className="font-medium">{project.target_company}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-muted-foreground">Created</p>
              <p className="font-medium">
                {new Date(project.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        <div className="grid gap-6">
          <div className="border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Chat</h2>
            <p className="text-muted-foreground mb-4">
              Interact with AI to analyze your project
            </p>
            <Link
              href={`/chat?project=${project.id}`}
              className="inline-block px-4 py-2 rounded-md bg-foreground text-background hover:bg-foreground/90"
            >
              Open Chat
            </Link>
          </div>

          <div className="border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Deliverables</h2>
            <p className="text-muted-foreground">
              No deliverables yet. Create them through the chat interface.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

function getStatusColor(status: string): string {
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
