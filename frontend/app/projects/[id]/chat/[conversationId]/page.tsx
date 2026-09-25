import ChatWindow from "../../../../../components/ChatWindow";

export default async function ConversationChatPage({
  params,
}: {
  params: Promise<{ id: string; conversationId: string }>;
}) {
  const { conversationId } = await params;

  return (
    <main className="flex min-h-screen flex-col p-8">
      <ChatWindow conversationId={Number(conversationId)} />
    </main>
  );
}
