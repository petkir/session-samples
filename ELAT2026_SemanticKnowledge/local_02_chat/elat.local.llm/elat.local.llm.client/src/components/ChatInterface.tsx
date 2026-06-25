import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Button, 
  ScrollArea, 
  Text, 
  Title,
  Stack,
  Group,
  Paper,
  Avatar,
  Textarea,
  ActionIcon,
  Badge,
  Box,
  Divider,
  Menu,
  Modal,
  TextInput
} from '@mantine/core';
import { 
  IconPlus, 
  IconMessageCircle, 
  IconUser, 
  IconRobot, 
  IconSend, 
  IconPaperclip,
  IconTrash,
  IconDots,
  IconEdit
} from '@tabler/icons-react';
import { chatApi } from '../services/chatApi';
import type { ChatSession, ChatMessage, ChatStreamResponse } from '../types/chat';
import FilePreview from './FilePreview';
import './ChatInterface.scss';

// Generate unique ID with timestamp and random component
const generateUniqueId = () => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

const ChatInterface = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<ChatSession | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  const loadSessions = useCallback(async () => {
    try {
      const sessionsData = await chatApi.getChatSessions();
      console.log('Loaded sessions:', sessionsData); // Debug log
      
      // Ensure sessionsData is an array
      if (Array.isArray(sessionsData)) {
        setSessions(sessionsData);
        if (sessionsData.length > 0 && !currentSession) {
          setCurrentSession(sessionsData[0]);
          console.log('Setting current session:', sessionsData[0]);
          setMessages(sessionsData[0].messages || []);
        }
      } else {
        console.error('Sessions data is not an array:', sessionsData);
        setSessions([]); // Set to empty array as fallback
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
      setSessions([]); // Set to empty array on error
    }
  }, [currentSession]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  // Debug modal state
  useEffect(() => {
    console.log('Modal state changed - deleteModalOpen:', deleteModalOpen, 'sessionToDelete:', sessionToDelete);
  }, [deleteModalOpen, sessionToDelete]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const createNewSession = async () => {
    try {
      const newSession = await chatApi.createChatSession({
        title: 'New Chat'
      });
      setSessions([newSession, ...sessions]);
      setCurrentSession(newSession);
      setMessages([]);
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const selectSession = async (session: ChatSession) => {
    try {
      const sessionData = await chatApi.getChatSession(session.id);
      setCurrentSession(sessionData);
      console.log('Selected session:', sessionData);
      setMessages(Array.isArray(sessionData.messages) ? sessionData.messages : []);
    } catch (error) {
      console.error('Error loading session:', error);
      // Fallback to basic session data
      setCurrentSession(session);
      setMessages([]);
    }
  };

  const handleDeleteSession = (session: ChatSession) => {
    console.log('Delete session triggered:', session);
    setSessionToDelete(session);
    setDeleteModalOpen(true);
    console.log('Modal should be open now, deleteModalOpen:', true);
  };

  const confirmDeleteSession = async () => {
    if (!sessionToDelete) return;

    try {
      await chatApi.deleteChatSession(sessionToDelete.id);
      
      // Remove the session from the list
      setSessions(prevSessions => prevSessions.filter(s => s.id !== sessionToDelete.id));
      
      // If the deleted session was the current session, clear it
      if (currentSession?.id === sessionToDelete.id) {
        setCurrentSession(null);
        setMessages([]);
      }
      
      setDeleteModalOpen(false);
      setSessionToDelete(null);
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const cancelDeleteSession = () => {
    setDeleteModalOpen(false);
    setSessionToDelete(null);
  };

  const handleEditSession = (session: ChatSession) => {
    setEditingSessionId(session.id);
    setEditingTitle(session.title);
  };

  const saveSessionTitle = async () => {
    if (!editingSessionId || !editingTitle.trim()) return;

    try {
      // Update the session title via API
      await chatApi.updateChatSession(editingSessionId, { title: editingTitle.trim() });
      
      // Update the sessions list locally
      setSessions(prevSessions => 
        prevSessions.map(session => 
          session.id === editingSessionId 
            ? { ...session, title: editingTitle.trim() }
            : session
        )
      );
      
      // Update current session if it's the one being edited
      if (currentSession?.id === editingSessionId) {
        setCurrentSession(prev => prev ? { ...prev, title: editingTitle.trim() } : null);
      }
      
      setEditingSessionId(null);
      setEditingTitle('');
    } catch (error) {
      console.error('Error updating session title:', error);
      // Reset editing state on error
      setEditingSessionId(null);
      setEditingTitle('');
    }
  };

  const cancelEditSession = () => {
    setEditingSessionId(null);
    setEditingTitle('');
  };

  const handleEditKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      saveSessionTitle();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      cancelEditSession();
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newFiles = Array.from(event.target.files || []);
    setSelectedFiles(prevFiles => [...prevFiles, ...newFiles]);
    
    // Clear the input so the same file can be selected again if needed
    if (event.target) {
      event.target.value = '';
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(files => files.filter((_, i) => i !== index));
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // Only set to false if we're leaving the drop zone entirely
    if (dropZoneRef.current && !dropZoneRef.current.contains(e.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      // Filter files to match the accepted types
      const acceptedFiles = files.filter(file => {
        const acceptedTypes = ['image/', 'application/pdf', 'application/msword', 
                              'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                              'text/plain'];
        return acceptedTypes.some(type => file.type.startsWith(type));
      });
      
      if (acceptedFiles.length > 0) {
        setSelectedFiles(prevFiles => [...prevFiles, ...acceptedFiles]);
      }
    }
  };

  const sendMessage = async () => {
    if (!currentSession || (!inputValue.trim() && selectedFiles.length === 0)) {
      return;
    }

    const messageContent = inputValue.trim();
    setInputValue('');
    setSelectedFiles([]);
    setIsLoading(true);
    setIsStreaming(true);
    setStreamingMessage('');

    // Add user message to UI immediately
    const userMessage: ChatMessage = {
      id: generateUniqueId(),
      role: 'user',
      content: messageContent,
      createdAt: new Date().toISOString(),
      attachments: selectedFiles.map((file, index) => ({
        id: `temp-${generateUniqueId()}-${index}`,
        fileName: file.name,
        contentType: file.type,
        fileSize: file.size,
        createdAt: new Date().toISOString()
      }))
    };
console.log('User message added:', userMessage);
    setMessages(prev => [...prev, userMessage]);

    try {
      const stream = await chatApi.sendMessage(currentSession.id, {
        content: messageContent,
        files: selectedFiles
      });

      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let isLastChunk = false;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data: ChatStreamResponse = JSON.parse(line.slice(6));
              
              if (data.Type === 'chunk') {
                isLastChunk = false;
                setStreamingMessage(prev => prev + data.Content);
              } else if (data.Type === 'complete') {
                // Add the completed assistant message to the conversation
                  setStreamingMessage(prevContent => {
                  const assistantMessageContent = prevContent + data.Content;
                const assistantMessage: ChatMessage = {
                    id: data.MessageId || generateUniqueId(),
                    role: 'assistant',
                    content: assistantMessageContent,
                    createdAt: new Date().toISOString(),
                    attachments: []
                  };
                 if(!isLastChunk) {
                  console.log('Assistant message completed:', assistantMessage);
                 setMessages(prev => [...prev, assistantMessage]);
                }
                 isLastChunk = true;
                 return ''; // Clear the streaming message
                });
                setIsStreaming(false);
                
                // Note: Not calling loadSessions() here to avoid duplicate messages
                // The message is already added manually above
              } else if (data.Type === 'error') {
                console.error('Streaming error:', data.Error);
                setIsStreaming(false);
                setStreamingMessage('');
              }
            } catch (error) {
              console.error('Error parsing SSE data:', error, 'Line:', line);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setIsStreaming(false);
      setStreamingMessage('');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="chat-interface">
      <div className="chat-sidebar">
        <div className="sidebar-content">
          <Button
            leftSection={<IconPlus size={16} />}
            variant="filled"
            onClick={createNewSession}
            fullWidth
            mb="md"
          >
            New Chat
          </Button>
          
          <Divider mb="md" />
          
          <ScrollArea className="sessions-scroll">
            <Stack gap="xs">
              {Array.isArray(sessions) && sessions.length > 0 ? (
                sessions.map((session) => (
                  <Paper
                    key={session.id}
                    p="sm"
                    withBorder
                    bg={currentSession?.id === session.id ? 'blue.1' : undefined}
                    style={{ cursor: 'pointer' }}
                  >
                    <Group gap="sm" wrap="nowrap">
                      <Group gap="sm" flex={1} onClick={() => selectSession(session)} style={{ cursor: 'pointer' }}>
                        <IconMessageCircle size={16} />
                        {editingSessionId === session.id ? (
                          <TextInput
                            value={editingTitle}
                            onChange={(e) => setEditingTitle(e.target.value)}
                            onKeyDown={handleEditKeyPress}
                            onBlur={saveSessionTitle}
                            size="xs"
                            style={{ flex: 1 }}
                            onClick={(e) => e.stopPropagation()}
                            autoFocus
                          />
                        ) : (
                          <Text size="sm" truncate>
                            {session.title}
                          </Text>
                        )}
                      </Group>
                      <Menu shadow="md" width={200}>
                        <Menu.Target>
                          <ActionIcon 
                            variant="subtle" 
                            color="gray" 
                            size="sm"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <IconDots size={14} />
                          </ActionIcon>
                        </Menu.Target>

                        <Menu.Dropdown>
                          <Menu.Item 
                            leftSection={<IconEdit size={14} />}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleEditSession(session);
                            }}
                          >
                            Edit Title
                          </Menu.Item>
                          <Menu.Item 
                            color="red" 
                            leftSection={<IconTrash size={14} />}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteSession(session);
                            }}
                          >
                            Delete Chat
                          </Menu.Item>
                        </Menu.Dropdown>
                      </Menu>
                    </Group>
                  </Paper>
                ))
              ) : (
                <Text size="sm" c="dimmed" ta="center">
                  No chat sessions yet. Create your first chat!
                </Text>
              )}
            </Stack>
          </ScrollArea>
        </div>
      </div>

      <div 
        className="chat-main"
        ref={dropZoneRef}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {isDragOver && (
          <div className="drag-overlay">
            <div className="drag-overlay-content">
              <IconPaperclip size={48} />
              <Text size="lg" fw={500}>Drop files here to attach</Text>
              <Text size="sm" c="dimmed">Supports images, PDF, Word documents, and text files</Text>
            </div>
          </div>
        )}
        
        <div className="chat-header">
          <Group justify="space-between">
            <Title order={2}>
              {currentSession?.title || 'Select a chat'}
            </Title>
           
          </Group>
        </div>

        <ScrollArea className="chat-messages">
          <Stack gap="md" p="md">
            {Array.isArray(messages) && messages.length > 0 ? (
              messages.map((message) => (
                <Group key={message.id} align="flex-start" gap="sm">
                  <Avatar color={message.role === 'user' ? 'blue' : 'green'} radius="xl">
                    {message.role === 'user' ? <IconUser size={20} /> : <IconRobot size={20} />}
                  </Avatar>
                  <Box flex={1}>
                    <Paper p="sm" withBorder>
                      <Text size="sm">
                        {message.content}
                      </Text>
                      {message.attachments && message.attachments.length > 0 && (
                        <Stack gap="xs" mt="xs">
                          {message.attachments.map((attachment) => (
                            <Badge
                              key={attachment.id}
                              variant="light"
                              leftSection={<IconPaperclip size={12} />}
                            >
                              {attachment.fileName} ({formatFileSize(attachment.fileSize)})
                            </Badge>
                          ))}
                        </Stack>
                      )}
                    </Paper>
                  </Box>
                </Group>
              ))
            ) : (
              <Text size="sm" c="dimmed" ta="center">
                {currentSession ? 'No messages yet. Start a conversation!' : 'Select a chat session to view messages'}
              </Text>
            )}
            
            {isStreaming && (
              <Group align="flex-start"  gap="sm">
                <Avatar color="red" radius="xl">
                  <IconRobot size={20} />
                </Avatar>
                <Box flex={1}>
                  <Paper p="sm" withBorder>
                    <Text size="sm">
                      {streamingMessage}
                      <span className="streaming-cursor">|</span>
                    </Text>
                  </Paper>
                </Box>
              </Group>
            )}
            
            <div ref={messagesEndRef} />
          </Stack>
        </ScrollArea>

        <div className="chat-input-section">
          <Paper p="md" withBorder>
            <Stack gap="sm">
              {selectedFiles.length > 0 && (
                <div className="file-preview-grid">
                  {selectedFiles.map((file, index) => (
                    <FilePreview
                      key={index}
                      file={file}
                      onRemove={() => removeFile(index)}
                    />
                  ))}
                </div>
              )}
              
              <Group gap="sm">
                <ActionIcon
                  size="lg"
                  variant="light"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isLoading}
                  aria-label="Attach file"
                >
                  <IconPaperclip size={18} />
                </ActionIcon>
                
                <Textarea
                  flex={1}
                  placeholder="Type your message..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyPress}
                  disabled={isLoading}
                  minRows={1}
                  maxRows={4}
                  autosize
                />
                
                <ActionIcon
                  size="lg"
                  variant="filled"
                  onClick={sendMessage}
                  disabled={isLoading || (!inputValue.trim() && selectedFiles.length === 0)}
                  aria-label="Send message"
                >
                  <IconSend size={18} />
                </ActionIcon>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileSelect}
                  multiple
                  accept="image/*,.pdf,.doc,.docx,.txt,.xml"
                  className="file-input-hidden"
                  aria-label="Select files to upload"
                />
              </Group>
            </Stack>
          </Paper>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        opened={deleteModalOpen}
        onClose={cancelDeleteSession}
        title="Delete Chat Session"
        centered
        zIndex={2000}
        overlayProps={{ blur: 3 }}
        withinPortal
        
      >
        <Stack gap="md">
          <Text>
            Are you sure you want to delete "{sessionToDelete?.title}"? This action cannot be undone.
          </Text>
          <Group justify="flex-end">
            <Button variant="default" onClick={cancelDeleteSession}>
              Cancel
            </Button>
            <Button color="red" onClick={confirmDeleteSession}>
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>
    </div>
  );
};

export default ChatInterface;
