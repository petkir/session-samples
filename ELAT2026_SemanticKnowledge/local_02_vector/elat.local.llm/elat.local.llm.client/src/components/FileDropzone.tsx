import { useState, useCallback, useRef, DragEvent } from 'react';
import { 
  Paper, 
  Text, 
  Group, 
  Button, 
  Stack, 
  Progress,
  Badge,
  ActionIcon,
  Tooltip,
  TextInput
} from '@mantine/core';
import { 
  IconUpload, 
  IconFile, 
  IconX,
  IconFileText
} from '@tabler/icons-react';
import './FileDropzone.scss';

interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  onUpload: (files: File[], category?: string) => Promise<void>;
  uploading?: boolean;
  maxFiles?: number;
  maxSize?: number; // in bytes
  accept?: string[];
}

interface FileWithPreview {
  file: File;
  id: string;
}

const getFileIcon = (fileName: string) => {
  const extension = fileName.toLowerCase().split('.').pop();
  switch (extension) {
    case 'pdf':
    case 'doc':
    case 'docx':
    case 'xls':
    case 'xlsx':
      return <IconFile size={20} color="blue" />;
    case 'txt':
    case 'md':
      return <IconFileText size={20} color="gray" />;
    default:
      return <IconFile size={20} />;
  }
};

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const FileDropzone = ({ 
  onFilesSelected, 
  onUpload, 
  uploading = false,
  maxFiles = 10,
  maxSize = 10 * 1024 * 1024, // 10MB default
  accept = ['.txt', '.md', '.pdf', '.doc', '.docx', '.json', '.csv']
}: FileDropzoneProps) => {
  const [selectedFiles, setSelectedFiles] = useState<FileWithPreview[]>([]);
  const [category, setCategory] = useState<string>('');
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFiles = useCallback((files: File[]) => {
    return files.filter(file => {
      if (file.size > maxSize) {
        return false;
      }
      const extension = '.' + file.name.split('.').pop()?.toLowerCase();
      return accept.includes(extension);
    });
  }, [maxSize, accept]);

  const handleFiles = useCallback((files: File[]) => {
    const validFiles = validateFiles(files);
    const newFiles = validFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
    }));
    
    setSelectedFiles(prev => [...prev, ...newFiles].slice(0, maxFiles));
    onFilesSelected(validFiles);
  }, [onFilesSelected, maxFiles, validateFiles]);

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!uploading) {
      setIsDragActive(true);
    }
  }, [uploading]);

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (uploading) return;
    
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  }, [uploading, handleFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      handleFiles(files);
    }
  }, [handleFiles]);

  const removeFile = useCallback((id: string) => {
    setSelectedFiles(prev => prev.filter(f => f.id !== id));
  }, []);

  const handleUpload = useCallback(async () => {
    if (selectedFiles.length === 0) return;
    
    const files = selectedFiles.map(f => f.file);
    await onUpload(files, category || undefined);
    setSelectedFiles([]);
    setCategory('');
  }, [selectedFiles, onUpload, category]);

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="file-dropzone">
      <Paper
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'disabled' : ''}`}
        withBorder
        p="xl"
        radius="md"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleBrowseClick}
        style={{ cursor: uploading ? 'not-allowed' : 'pointer' }}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={accept.join(',')}
          onChange={handleFileSelect}
          className="file-input-hidden"
          disabled={uploading}
          aria-label="Select files to upload"
        />
        <Group justify="center" gap="xl" className="dropzone-content">
          <div>
            <IconUpload size={48} stroke={1.5} />
          </div>
          <div>
            <Text size="xl" inline>
              {isDragActive ? 'Drop files here' : 'Drag files here or click to browse'}
            </Text>
            <Text size="sm" c="dimmed" inline mt={7}>
              Upload documents to add to the knowledge base
            </Text>
            <Text size="xs" c="dimmed" mt={4}>
              Supported formats: {accept.join(', ')} (max {formatFileSize(maxSize)})
            </Text>
          </div>
        </Group>
      </Paper>

      {selectedFiles.length > 0 && (
        <Stack gap="md" mt="md">
          <Text fw={500}>Selected Files ({selectedFiles.length})</Text>
          
          {selectedFiles.map(({ file, id }) => (
            <Paper key={id} p="md" withBorder radius="md">
              <Group justify="space-between">
                <Group gap="sm">
                  {getFileIcon(file.name)}
                  <div>
                    <Text size="sm" fw={500}>
                      {file.name}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {formatFileSize(file.size)}
                    </Text>
                  </div>
                  <Badge size="sm" variant="light">
                    {file.type || 'Unknown type'}
                  </Badge>
                </Group>
                
                <Tooltip label="Remove file">
                  <ActionIcon
                    variant="subtle"
                    color="red"
                    onClick={() => removeFile(id)}
                    disabled={uploading}
                  >
                    <IconX size={16} />
                  </ActionIcon>
                </Tooltip>
              </Group>
            </Paper>
          ))}

          <Group gap="md" mt="md">
            <TextInput
              placeholder="Category (optional)"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              style={{ flex: 1 }}
              disabled={uploading}
            />
            <Button
              onClick={handleUpload}
              loading={uploading}
              disabled={selectedFiles.length === 0}
              leftSection={<IconUpload size={16} />}
            >
              Upload {selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''}
            </Button>
          </Group>

          {uploading && (
            <Progress value={100} animated />
          )}
        </Stack>
      )}
    </div>
  );
};

export default FileDropzone;
