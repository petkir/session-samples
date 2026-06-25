import { 
  Text, 
  ActionIcon, 
  Image, 
  Paper, 
  Stack,
  Box,
  Center
} from '@mantine/core';
import { 
  IconX, 
  IconFile, 
  IconFileText, 
  IconPhoto,
  IconFileTypePdf
} from '@tabler/icons-react';
import './FilePreview.scss';

interface FilePreviewProps {
  file: File;
  onRemove: () => void;
}

const FilePreview = ({ file, onRemove }: FilePreviewProps) => {
  const isImage = file.type.startsWith('image/');
  const isPDF = file.type === 'application/pdf';
  const isText = file.type.startsWith('text/') || 
                 file.type === 'application/msword' || 
                 file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = () => {
    if (isImage) return <IconPhoto size={16} />;
    if (isPDF) return <IconFileTypePdf size={16} />;
    if (isText) return <IconFileText size={16} />;
    return <IconFile size={16} />;
  };

  return (
    <Paper 
      className="file-preview" 
      p="md" 
      withBorder 
      radius="md"
      style={{ position: 'relative', minWidth: 200, maxWidth: 250 }}
    >
        {/* Remove button */}
        <ActionIcon
          size="sm"
          color="red"
          radius="xl"
          variant="filled"
          style={{ 
            position: 'absolute', 
            top: -8, 
            right: -8, 
            zIndex: 10 
          }}
          onClick={onRemove}
        >
          <IconX size={12} />
        </ActionIcon>

        <Stack gap="sm">
          {/* File preview area */}
          <Box style={{ position: 'relative' }}>
            {isImage ? (
              <div className="image-preview-container">
                <Image
                  src={URL.createObjectURL(file)}
                  alt={file.name}
                  height={120}
                  fit="cover"
                  radius="sm"
                  onLoad={(e) => {
                    // Clean up the object URL after the image loads
                    const img = e.target as HTMLImageElement;
                    setTimeout(() => {
                      if (img.src.startsWith('blob:')) {
                        URL.revokeObjectURL(img.src);
                      }
                    }, 100);
                  }}
                />
              </div>
            ) : (
              <Center h={120} style={{ backgroundColor: 'var(--mantine-color-gray-1)' }}>
                <Stack align="center" gap="xs">
                  {getFileIcon()}
                  <Text size="xs" c="dimmed" ta="center">
                    {isPDF ? 'PDF Document' : 
                     isText ? 'Text Document' : 
                     'File'}
                  </Text>
                </Stack>
              </Center>
            )}
          </Box>

          {/* File info */}
          <Box>
            <Text size="sm" fw={500} lineClamp={2} title={file.name}>
              {file.name}
            </Text>
            <Text size="xs" c="dimmed">
              {formatFileSize(file.size)}
            </Text>
          </Box>
        </Stack>
      </Paper>
  );
};

export default FilePreview;
