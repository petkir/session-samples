import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { Container, Text, Title } from '@mantine/core';
import ChatInterface from './ChatInterface';
import { chatApi } from '../services/chatApi';
import type { ChatSession } from '../types/chat';
import Loading from './Loading';

const ChatWrapper = () => {
  const { chatId } = useParams<{ chatId: string }>();
  const navigate = useNavigate();
  const [initialSession, setInitialSession] = useState<ChatSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeChat = async () => {
      setIsLoading(true);
      setError(null);

      try {
        if (chatId === 'new') {
          // Create new session
          const newSession = await chatApi.createChatSession({
            title: 'New Chat'
          });
          // Redirect to the new session URL
          navigate(`/chat/${newSession.id}`, { replace: true });
          setInitialSession(newSession);
        } else if (chatId) {
          // Load existing session
          try {
            const sessionData = await chatApi.getChatSession(chatId);
            setInitialSession(sessionData);
          } catch (error) {
            console.error('Error loading chat session:', error);
            setError('Chat session not found');
            // Redirect to description page after a delay
            setTimeout(() => navigate('/', { replace: true }), 2000);
          }
        } else {
          // No chat ID provided, stay on description page
          setInitialSession(null);
        }
      } catch (error) {
        console.error('Error initializing chat:', error);
        setError('Failed to initialize chat');
      } finally {
        setIsLoading(false);
      }
    };

    initializeChat();
  }, [chatId, navigate]);

  if (isLoading) {
    return <Loading />;
  }

  if (error) {
    return (
      <Container size="md" py="xl">
        <Title order={3} ta="center" c="red">Error: {error}</Title>
        <Text ta="center" mt="md">Redirecting to home page...</Text>
      </Container>
    );
  }

  return <ChatInterface initialSession={initialSession} />;
};

export default ChatWrapper;
