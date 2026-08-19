import ChatWindow from "../../../../components/ChatWindow";

export default async function ProjectChatPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const projectId = Number(id);

  return (
    <main className="flex min-h-screen flex-col p-8">
      <ChatWindow projectId={projectId} />
    </main>
  );
}
