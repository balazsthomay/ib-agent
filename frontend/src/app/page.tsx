import { SignInButton, SignUpButton, UserButton, SignedIn, SignedOut } from '@clerk/nextjs'
import Link from 'next/link'

export default function Home() {
  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <header className="row-start-1 w-full flex justify-between items-center">
        <h1 className="text-2xl font-bold">IB Agent</h1>
        <div className="flex gap-4 items-center">
          <SignedOut>
            <SignInButton mode="modal">
              <button className="px-4 py-2 rounded-md border border-solid border-black/[.08] dark:border-white/[.145] hover:bg-[#f2f2f2] dark:hover:bg-[#1a1a1a] hover:border-transparent">
                Sign In
              </button>
            </SignInButton>
            <SignUpButton mode="modal">
              <button className="px-4 py-2 rounded-md bg-foreground text-background hover:bg-[#383838] dark:hover:bg-[#ccc]">
                Sign Up
              </button>
            </SignUpButton>
          </SignedOut>
          <SignedIn>
            <Link
              href="/dashboard"
              className="px-4 py-2 rounded-md border border-solid border-transparent hover:bg-[#f2f2f2] dark:hover:bg-[#1a1a1a]"
            >
              Dashboard
            </Link>
            <UserButton />
          </SignedIn>
        </div>
      </header>

      <main className="flex flex-col gap-8 row-start-2 items-center text-center">
        <h2 className="text-4xl font-bold sm:text-6xl">
          AI Platform for<br />Investment Banking
        </h2>
        <p className="text-lg text-center max-w-2xl">
          Automate target screening, trading comps, and public information books
          for small-mid cap European investment banks.
        </p>

        <SignedOut>
          <div className="flex gap-4 items-center flex-col sm:flex-row">
            <SignUpButton mode="modal">
              <button className="px-6 py-3 text-lg rounded-md bg-foreground text-background hover:bg-[#383838] dark:hover:bg-[#ccc]">
                Get Started
              </button>
            </SignUpButton>
            <SignInButton mode="modal">
              <button className="px-6 py-3 text-lg rounded-md border border-solid border-black/[.08] dark:border-white/[.145] hover:bg-[#f2f2f2] dark:hover:bg-[#1a1a1a]">
                Sign In
              </button>
            </SignInButton>
          </div>
        </SignedOut>

        <SignedIn>
          <Link
            href="/dashboard"
            className="px-6 py-3 text-lg rounded-md bg-foreground text-background hover:bg-[#383838] dark:hover:bg-[#ccc]"
          >
            Go to Dashboard
          </Link>
        </SignedIn>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-8 text-left max-w-4xl">
          <div className="p-6 rounded-lg border border-solid border-black/[.08] dark:border-white/[.145]">
            <h3 className="font-semibold text-lg mb-2">Target Screening</h3>
            <p className="text-sm opacity-80">AI-powered M&A target discovery and analysis</p>
          </div>
          <div className="p-6 rounded-lg border border-solid border-black/[.08] dark:border-white/[.145]">
            <h3 className="font-semibold text-lg mb-2">Trading Comps</h3>
            <p className="text-sm opacity-80">Automated comparable company analysis</p>
          </div>
          <div className="p-6 rounded-lg border border-solid border-black/[.08] dark:border-white/[.145]">
            <h3 className="font-semibold text-lg mb-2">Public Info Books</h3>
            <p className="text-sm opacity-80">Comprehensive company research reports</p>
          </div>
        </div>
      </main>

      <footer className="row-start-3 flex gap-6 flex-wrap items-center justify-center">
        <p className="text-sm opacity-50">IB Agent © 2025</p>
      </footer>
    </div>
  );
}
