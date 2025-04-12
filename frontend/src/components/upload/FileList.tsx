'use client';

import { useState, useEffect } from 'react';
import { File, Image, Trash2, RefreshCcw, ExternalLink } from 'lucide-react';
import { useAuth } from '@/context/auth-context';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { formatBytes } from '@/lib/utils';
import { useParams } from 'next/navigation';
import { getDictionary } from '@/lib/dictionary';
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface FileItem {
  id?: number;
  filename: string;
  original_filename?: string;
  type: 'document' | 'image';
  size: number;
  last_modified: string;
  content_type?: string;
}

interface FileListProps {
  onSelect?: (file: FileItem) => void;
  className?: string;
}

export function FileList({ onSelect, className = '' }: FileListProps) {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [fileToDelete, setFileToDelete] = useState<FileItem | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const { token } = useAuth();
  const { toast } = useToast();
  
  const params = useParams();
  const lang = (params?.lang as string) || "en";
  const dictionary = getDictionary(lang);
  const t = dictionary.chat;
  
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const API_V1_URL = `${API_BASE_URL}/api/v1`;

  const fetchFiles = async () => {
    if (!token) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`${API_V1_URL}/files/files`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch files');
      }

      const data = await response.json();
      setFiles(data.files || []);
    } catch (error: any) {
      toast({
        title: t.file?.fetch_error || 'Error fetching files',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, [token]);

  const handleRefresh = () => {
    fetchFiles();
  };

  const handleSelect = (file: FileItem) => {
    if (onSelect) {
      onSelect(file);
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, file: FileItem) => {
    e.stopPropagation();
    setFileToDelete(file);
    setShowDeleteDialog(true);
  };

  const confirmDelete = async () => {
    if (!fileToDelete || !fileToDelete.id) return;
    
    setIsDeleting(true);
    try {
      const response = await fetch(`${API_V1_URL}/files/files/${fileToDelete.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete file');
      }

      // 成功删除后，更新文件列表
      setFiles(files.filter(f => f.id !== fileToDelete.id));
      
      toast({
        title: t.file?.delete_success || 'File deleted',
        description: t.file?.delete_success_message || 'The file has been successfully deleted.',
        variant: 'default',
      });
    } catch (error: any) {
      toast({
        title: t.file?.delete_error || 'Error deleting file',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsDeleting(false);
      setShowDeleteDialog(false);
      setFileToDelete(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getDisplayFilename = (file: FileItem) => {
    return file.original_filename || file.filename;
  };

  if (!token) {
    return (
      <div className="text-center p-4">
        {t.login?.title || 'Please log in to view your files.'}
      </div>
    );
  }

  return (
    <>
      <div className={`border rounded-lg p-4 ${className}`}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">{t.file?.title || 'Your Files'}</h3>
          <Button variant="ghost" size="sm" onClick={handleRefresh}>
            <RefreshCcw size={16} className="mr-2" />
            {t.file?.refresh || 'Refresh'}
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center space-x-4">
                <Skeleton className="h-12 w-12" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-[250px]" />
                  <Skeleton className="h-4 w-[200px]" />
                </div>
              </div>
            ))}
          </div>
        ) : files.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            {t.file?.no_files || 'No files uploaded yet. Upload files to see them here.'}
          </div>
        ) : (
          <div className="space-y-2">
            {files.map((file) => (
              <div
                key={file.filename}
                className="flex items-center justify-between p-2 rounded-md hover:bg-muted cursor-pointer"
                onClick={() => handleSelect(file)}
              >
                <div className="flex items-center space-x-3">
                  {file.type === 'document' ? (
                    <File size={24} className="text-blue-500" />
                  ) : (
                    <Image size={24} className="text-green-500" />
                  )}
                  <div>
                    <p className="font-medium truncate max-w-[200px]" title={getDisplayFilename(file)}>
                      {getDisplayFilename(file)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatBytes(file.size)} • {formatDate(file.last_modified)}
                    </p>
                  </div>
                </div>
                <div className="flex space-x-1">
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                    onClick={(e) => handleDeleteClick(e, file)}
                  >
                    <Trash2 size={16} />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 删除确认对话框 */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t.file?.delete_confirm_title || 'Delete File'}</AlertDialogTitle>
            <AlertDialogDescription>
              {t.file?.delete_confirm_message || 'Are you sure you want to delete this file? This action cannot be undone.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.file?.cancel || 'Cancel'}</AlertDialogCancel>
            <AlertDialogAction 
              onClick={confirmDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? 
                (t.file?.deleting || 'Deleting...') : 
                (t.file?.delete || 'Delete')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
} 