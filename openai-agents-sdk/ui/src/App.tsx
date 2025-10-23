import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ChatContainer from "./components/chat/ChatContainer";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ChatContainer />
    </QueryClientProvider>
  );
}

export default App;
