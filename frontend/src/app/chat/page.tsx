import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { UserButton } from '@clerk/nextjs'
import Link from 'next/link'

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
          <div className="flex-1 flex flex-col p-4 overflow-y-auto bg-muted/20">
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center text-muted-foreground">
                <p className="text-lg mb-2">Chat interface coming soon</p>
                <p className="text-sm">
                  This will connect to the backend chat API with WebSocket support
                </p>
              </div>
            </div>
          </div>

          <div className="border-t border-border p-4 bg-background">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Type your message... (disabled)"
                disabled
                className="flex-1 px-4 py-2 rounded-md border border-border bg-muted/50 cursor-not-allowed"
              />
              <button
                disabled
                className="px-6 py-2 rounded-md bg-foreground/50 text-background cursor-not-allowed"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
