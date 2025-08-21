import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ChatContainer from './components/chat/ChatContainer';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="h-screen bg-gray-50">
        <ChatContainer />
      </div>
    </QueryClientProvider>
  );
}

export default App
