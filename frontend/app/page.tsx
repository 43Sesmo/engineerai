import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-4xl font-bold text-center">EngineerAI</h1>
      <Link href="/projects" className="text-blue-600 underline">
        View Projects
      </Link>
    </main>
  );
}
