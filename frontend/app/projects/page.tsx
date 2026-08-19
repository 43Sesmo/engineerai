import ProjectList from "../../components/ProjectList";

export default function ProjectsPage() {
  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <h1 className="text-3xl font-bold mb-6">Projects</h1>
      <ProjectList />
    </main>
  );
}
