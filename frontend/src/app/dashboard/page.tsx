import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { getProjects } from '@/lib/api'
import { ProjectList } from '@/components/project-list'
import { CreateProjectButton } from '@/components/create-project-button'
import { UserButton } from '@clerk/nextjs'
import Link from 'next/link'

export default async function DashboardPage() {
  const { getToken, userId } = await auth()

  if (!userId) {
    redirect('/')
  }

  const token = await getToken()
  if (!token) {
    redirect('/')
  }

  let projects: Awaited<ReturnType<typeof getProjects>> = []
  let error: string | null = null

  try {
    projects = await getProjects(token)
  } catch (e) {
    error = e instanceof Error ? e.message : 'Failed to load projects'
    console.error('Error loading projects:', e)
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold">
            IB Agent
          </Link>
          <div className="flex gap-4 items-center">
            <Link
              href="/dashboard"
              className="px-4 py-2 text-sm font-medium"
            >
              Dashboard
            </Link>
            <UserButton />
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Projects</h1>
            <p className="text-muted-foreground">
              Manage your investment banking projects
            </p>
          </div>
          <CreateProjectButton />
        </div>

        {error ? (
          <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-lg">
            {error}
          </div>
        ) : (
          <ProjectList projects={projects} />
        )}
      </main>
    </div>
  )
}
