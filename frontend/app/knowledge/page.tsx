import KnowledgeList from "../../components/KnowledgeList";

export default function KnowledgePage() {
  return (
    <main className="flex min-h-screen flex-col items-center gap-6 p-8">
      <h1 className="text-3xl font-bold">Knowledge Vault</h1>
      <KnowledgeList />
    </main>
  );
}
