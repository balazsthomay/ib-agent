import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { UserButton } from '@clerk/nextjs'
import Link from 'next/link'
import { ChatInterface } from '@/components/chat-interface'

interface ChatPageProps {
  searchParams: Promise<{
    project?: string
  }>
}

export default async function ChatPage({ searchParams }: ChatPageProps) {
  const { userId } = await auth()

  if (!userId) {
    redirect('/')
  }

  const { project: projectId } = await searchParams

  if (!projectId) {
    redirect('/dashboard')
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="border-b border-border">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold">
            IB Agent
          </Link>
          <div className="flex gap-4 items-center">
            <Link href="/dashboard" className="px-4 py-2 text-sm font-medium">
              Dashboard
            </Link>
            <Link
              href={`/projects/${projectId}`}
              className="px-4 py-2 text-sm font-medium"
            >
              Project Details
            </Link>
            <UserButton />
          </div>
        </div>
      </header>

      <main className="flex-1 flex flex-col container mx-auto px-4 py-8">
        <div className="mb-6">
          <Link
            href={`/projects/${projectId}`}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← Back to Project
          </Link>
        </div>

        <div className="flex-1 flex flex-col border border-border rounded-lg overflow-hidden">
          <ChatInterface projectId={projectId} />
        </div>
      </main>
    </div>
  )
}
