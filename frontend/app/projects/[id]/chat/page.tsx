import ConversationList from "../../../../components/ConversationList";

export default async function ProjectConversationsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const projectId = Number(id);

  return (
    <main className="flex min-h-screen flex-col p-8">
      <ConversationList projectId={projectId} />
    </main>
  );
}
