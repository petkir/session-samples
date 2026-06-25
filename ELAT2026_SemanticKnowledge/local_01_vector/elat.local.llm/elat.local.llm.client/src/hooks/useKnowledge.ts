import { useState, useCallback } from 'react';
import { knowledgeApi } from '../services/knowledgeApi';
import type { 
  KnowledgeSearchResult, 
  AddDocumentRequest, 
  SearchRequest 
} from '../types/knowledge';
import { notifications } from '@mantine/notifications';

export const useKnowledge = () => {
  const [documents, setDocuments] = useState<KnowledgeSearchResult[]>([]);
  const [searchResults, setSearchResults] = useState<KnowledgeSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const loadAllDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const results = await knowledgeApi.getAllDocuments();
      setDocuments(results);
    } catch (error) {
      console.error('Error loading documents:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to load documents',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  }, []);

  const searchDocuments = useCallback(async (request: SearchRequest) => {
    setLoading(true);
    try {
      const response = await knowledgeApi.search(request);
      setSearchResults(response.results);
      return response;
    } catch (error) {
      console.error('Error searching documents:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to search documents',
        color: 'red',
      });
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const addDocument = useCallback(async (request: AddDocumentRequest) => {
    setUploading(true);
    try {
      const response = await knowledgeApi.addDocument(request);
      notifications.show({
        title: 'Success',
        message: response.message,
        color: 'green',
      });
      // Reload documents to show the new one
      await loadAllDocuments();
      return response;
    } catch (error) {
      console.error('Error adding document:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to add document',
        color: 'red',
      });
      throw error;
    } finally {
      setUploading(false);
    }
  }, [loadAllDocuments]);

  const uploadFile = useCallback(async (file: File, category?: string) => {
    setUploading(true);
    try {
      const response = await knowledgeApi.uploadFile(file, category);
      notifications.show({
        title: 'Success',
        message: response.message,
        color: 'green',
      });
      // Reload documents to show the new one
      await loadAllDocuments();
      return response;
    } catch (error) {
      console.error('Error uploading file:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to upload file',
        color: 'red',
      });
      throw error;
    } finally {
      setUploading(false);
    }
  }, [loadAllDocuments]);

  const deleteDocument = useCallback(async (documentId: string) => {
    try {
      await knowledgeApi.deleteDocument(documentId);
      notifications.show({
        title: 'Success',
        message: 'Document deleted successfully',
        color: 'green',
      });
      // Reload documents to remove the deleted one
      await loadAllDocuments();
    } catch (error) {
      console.error('Error deleting document:', error);
      notifications.show({
        title: 'Error',
        message: 'Failed to delete document',
        color: 'red',
      });
      throw error;
    }
  }, [loadAllDocuments]);

  return {
    documents,
    searchResults,
    loading,
    uploading,
    loadAllDocuments,
    searchDocuments,
    addDocument,
    uploadFile,
    deleteDocument,
  };
};
