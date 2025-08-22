import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ChatContainer from "./components/chat/ChatContainer";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div style={{ height: "100vh", backgroundColor: "#ffffff" }}>
        <ChatContainer />
      </div>
    </QueryClientProvider>
  );
}

export default App;
