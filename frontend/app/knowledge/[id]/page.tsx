import KnowledgeEntryDetail from "../../../components/KnowledgeEntryDetail";

export default async function KnowledgeEntryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <main className="flex min-h-screen flex-col items-center gap-6 p-8">
      <KnowledgeEntryDetail entryId={Number(id)} />
    </main>
  );
}
