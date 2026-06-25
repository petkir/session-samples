import { useEffect, useState } from 'react';
import {
  Container,
  Title,
  Text,
  Grid,
  Paper,
  Stack,
  Group,
  Button,
  TextInput,
  ActionIcon,
  Tooltip,
  Badge,
  Loader,
  Tabs,
  ScrollArea,
  Modal,
  Code,
} from '@mantine/core';
import {
  IconSearch,
  IconRefresh,
  IconTrash,
  IconEye,
  IconDatabase,
  IconUpload,
  IconFileText,
  IconCalendar,
} from '@tabler/icons-react';
import { useKnowledge } from '../hooks/useKnowledge';
import FileDropzone from './FileDropzone';
import type { KnowledgeSearchResult } from '../types/knowledge';
import './Knowledge.scss';

const Knowledge = () => {
  const {
    documents,
    searchResults,
    loading,
    uploading,
    loadAllDocuments,
    searchDocuments,
    uploadFile,
    deleteDocument,
  } = useKnowledge();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('browse');
  const [selectedDocument, setSelectedDocument] = useState<KnowledgeSearchResult | null>(null);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);

  useEffect(() => {
    loadAllDocuments();
  }, [loadAllDocuments]);

  const handleSearch = async () => {
    if (searchQuery.trim()) {
      await searchDocuments({
        query: searchQuery,
        maxResults: 20,
      });
      setActiveTab('search');
    }
  };

  const handleUpload = async (files: File[], category?: string) => {
    for (const file of files) {
      await uploadFile(file, category);
    }
  };

  const handleDelete = async (documentId: string) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      await deleteDocument(documentId);
    }
  };

  const handlePreview = (document: KnowledgeSearchResult) => {
    setSelectedDocument(document);
    setPreviewModalOpen(true);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Unknown';
    }
  };

  const DocumentCard = ({ document }: { document: KnowledgeSearchResult }) => (
    <Paper p="md" withBorder radius="md" className="document-card">
      <Stack gap="sm">
        <Group justify="space-between" align="flex-start">
          <div className="document-content">
            <Group gap="xs" mb="xs">
              <IconFileText size={16} />
              <Text fw={500} size="sm" lineClamp={1}>
                {document.fileName || `Document ${document.documentId.substring(0, 8)}`}
              </Text>
            </Group>
            
            {document.category && (
              <Badge size="xs" variant="light" mb="xs">
                {document.category}
              </Badge>
            )}
            
            <Text size="xs" c="dimmed" lineClamp={3}>
              {document.content.substring(0, 150)}
              {document.content.length > 150 && '...'}
            </Text>
            
            <Group gap="xs" mt="xs">
              <IconCalendar size={12} />
              <Text size="xs" c="dimmed">
                {formatDate(document.addedAt)}
              </Text>
              {document.relevanceScore !== undefined && (
                <>
                  <Text size="xs" c="dimmed">•</Text>
                  <Text size="xs" c="dimmed">
                    {Math.round(document.relevanceScore * 100)}% match
                  </Text>
                </>
              )}
            </Group>
          </div>
          
          <Group gap="xs">
            <Tooltip label="Preview content">
              <ActionIcon
                variant="subtle"
                size="sm"
                onClick={() => handlePreview(document)}
              >
                <IconEye size={14} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Delete document">
              <ActionIcon
                variant="subtle"
                color="red"
                size="sm"
                onClick={() => handleDelete(document.documentId)}
              >
                <IconTrash size={14} />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>
      </Stack>
    </Paper>
  );

  return (
    <Container size="xl" py="md" className="knowledge-page">
      <Stack gap="xl">
        {/* Header */}
        <div>
          <Group justify="space-between" align="flex-end">
            <div>
              <Title order={2} mb="xs">
                <Group gap="sm">
                  <IconDatabase size={28} />
                  Knowledge Base
                </Group>
              </Title>
              <Text c="dimmed">
                Manage your document collection and search through your knowledge base
              </Text>
            </div>
            <Button
              leftSection={<IconRefresh size={16} />}
              variant="light"
              onClick={loadAllDocuments}
              loading={loading}
            >
              Refresh
            </Button>
          </Group>
        </div>

        {/* Search Bar */}
        <Paper p="md" withBorder radius="md">
          <Group gap="md">
            <TextInput
              placeholder="Search through your knowledge base..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              leftSection={<IconSearch size={16} />}
              style={{ flex: 1 }}
            />
            <Button
              onClick={handleSearch}
              loading={loading}
              disabled={!searchQuery.trim()}
              leftSection={<IconSearch size={16} />}
            >
              Search
            </Button>
          </Group>
        </Paper>

        {/* Tabs */}
        <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'browse')}>
          <Tabs.List>
            <Tabs.Tab value="browse" leftSection={<IconDatabase size={14} />}>
              Browse All ({documents.length})
            </Tabs.Tab>
            <Tabs.Tab value="search" leftSection={<IconSearch size={14} />}>
              Search Results {searchResults.length > 0 && `(${searchResults.length})`}
            </Tabs.Tab>
            <Tabs.Tab value="upload" leftSection={<IconUpload size={14} />}>
              Upload Files
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="browse" pt="md">
            <Stack gap="md">
              <Text size="sm" c="dimmed">
                All documents in your knowledge base
              </Text>
              
              {loading ? (
                <Group justify="center" py="xl">
                  <Loader size="md" />
                  <Text>Loading documents...</Text>
                </Group>
              ) : documents.length === 0 ? (
                <Paper p="xl" withBorder radius="md" ta="center">
                  <Stack gap="md" align="center">
                    <IconFileText size={48} stroke={1} color="gray" />
                    <div>
                      <Text size="lg" fw={500}>No documents found</Text>
                      <Text size="sm" c="dimmed">
                        Upload some files to get started with your knowledge base
                      </Text>
                    </div>
                    <Button 
                      onClick={() => setActiveTab('upload')}
                      leftSection={<IconUpload size={16} />}
                    >
                      Upload Files
                    </Button>
                  </Stack>
                </Paper>
              ) : (
                <Grid>
                  {documents.map((document) => (
                    <Grid.Col key={document.documentId} span={{ base: 12, md: 6, lg: 4 }}>
                      <DocumentCard document={document} />
                    </Grid.Col>
                  ))}
                </Grid>
              )}
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="search" pt="md">
            <Stack gap="md">
              {searchQuery ? (
                <Text size="sm" c="dimmed">
                  Search results for "{searchQuery}"
                </Text>
              ) : (
                <Text size="sm" c="dimmed">
                  Enter a search query to find relevant documents
                </Text>
              )}
              
              {loading ? (
                <Group justify="center" py="xl">
                  <Loader size="md" />
                  <Text>Searching...</Text>
                </Group>
              ) : searchResults.length === 0 && searchQuery ? (
                <Paper p="xl" withBorder radius="md" ta="center">
                  <Stack gap="md" align="center">
                    <IconSearch size={48} stroke={1} color="gray" />
                    <div>
                      <Text size="lg" fw={500}>No results found</Text>
                      <Text size="sm" c="dimmed">
                        Try different keywords or check your spelling
                      </Text>
                    </div>
                  </Stack>
                </Paper>
              ) : (
                <Grid>
                  {searchResults.map((document) => (
                    <Grid.Col key={document.documentId} span={{ base: 12, md: 6, lg: 4 }}>
                      <DocumentCard document={document} />
                    </Grid.Col>
                  ))}
                </Grid>
              )}
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="upload" pt="md">
            <Stack gap="md">
              <Text size="sm" c="dimmed">
                Upload new documents to add them to your knowledge base
              </Text>
              
              <FileDropzone
                onFilesSelected={() => {}} // We handle this in onUpload
                onUpload={handleUpload}
                uploading={uploading}
                maxFiles={5}
                maxSize={10 * 1024 * 1024} // 10MB
                accept={['.txt', '.md', '.pdf', '.doc', '.docx', '.json', '.csv']}
              />
            </Stack>
          </Tabs.Panel>
        </Tabs>
      </Stack>

      {/* Preview Modal */}
      <Modal
        opened={previewModalOpen}
        onClose={() => setPreviewModalOpen(false)}
        title="Document Preview"
        size="lg"
      >
        {selectedDocument && (
          <Stack gap="md">
            <Group justify="space-between">
              <div>
                <Text fw={500}>
                  {selectedDocument.fileName || `Document ${selectedDocument.documentId.substring(0, 8)}`}
                </Text>
                <Text size="sm" c="dimmed">
                  Added: {formatDate(selectedDocument.addedAt)}
                </Text>
              </div>
              {selectedDocument.category && (
                <Badge variant="light">{selectedDocument.category}</Badge>
              )}
            </Group>
            
            <ScrollArea h={400}>
              <Code block>{selectedDocument.content}</Code>
            </ScrollArea>
          </Stack>
        )}
      </Modal>
    </Container>
  );
};

export default Knowledge;
