'use client';

import { useState, useRef } from 'react';
import { UploadCloud, File, Image } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/auth-context';
import { useToast } from '@/hooks/use-toast';
import { useParams } from 'next/navigation';
import { getDictionary } from '@/lib/dictionary';

interface FileUploadButtonProps {
  onUploadSuccess?: (fileData: any) => void;
  acceptedFileTypes?: 'document' | 'image' | 'all';
  className?: string;
}

export function FileUploadButton({
  onUploadSuccess,
  acceptedFileTypes = 'all',
  className = '',
}: FileUploadButtonProps) {
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const { token } = useAuth();
  
  // 添加国际化支持
  const params = useParams();
  const lang = (params?.lang as string) || "en";
  const dictionary = getDictionary(lang);
  const t = dictionary.chat;
  
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const API_V1_URL = `${API_BASE_URL}/api/v1`;

  const getAcceptedTypes = () => {
    switch (acceptedFileTypes) {
      case 'document':
        return '.pdf,.docx,.txt,.md,.csv,.json';
      case 'image':
        return '.jpg,.jpeg,.png,.gif,.bmp,.webp';
      case 'all':
      default:
        return '.pdf,.docx,.txt,.md,.csv,.json,.jpg,.jpeg,.png,.gif,.bmp,.webp';
    }
  };

  const getEndpoint = (file: File) => {
    const fileExt = file.name.split('.').pop()?.toLowerCase() || '';
    const documentTypes = ['pdf', 'docx', 'txt', 'md', 'csv', 'json'];
    const imageTypes = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];
    
    if (documentTypes.includes(fileExt)) {
      return `${API_V1_URL}/files/upload/document`;
    } else if (imageTypes.includes(fileExt)) {
      return `${API_V1_URL}/files/upload/image`;
    }
    
    throw new Error('Unsupported file type');
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const endpoint = getEndpoint(file);
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload file');
      }

      const responseData = await response.json();
      
      toast({
        title: t.file?.upload_success || 'File uploaded successfully',
        description: `${file.name} ${t.file?.upload_success ? '' : 'has been uploaded.'}`,
        variant: 'default',
      });

      if (onUploadSuccess) {
        onUploadSuccess(responseData);
      }
    } catch (error: any) {
      toast({
        title: t.file?.upload_fail || 'Upload failed',
        description: error.message || 'Something went wrong during file upload',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
      // Reset the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // 获取按钮文本的函数
  const getButtonText = () => {
    if (isUploading) {
      return t.file?.uploading || 'Uploading...';
    }
    
    if (acceptedFileTypes === 'document') {
      return t.file?.upload_document || 'Upload document';
    } else if (acceptedFileTypes === 'image') {
      return t.file?.upload_image || 'Upload image';
    } else {
      return t.file?.upload || 'Upload file';
    }
  };

  return (
    <div className={className}>
      <input
        type="file"
        accept={getAcceptedTypes()}
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />
      <Button
        onClick={handleClick}
        variant="outline"
        disabled={isUploading}
        className="flex items-center gap-2"
        type="button"
      >
        {isUploading ? (
          <div className="flex items-center gap-2">
            <div className="animate-spin">
              <UploadCloud size={18} />
            </div>
            <span>{t.file?.uploading || 'Uploading...'}</span>
          </div>
        ) : (
          <>
            {acceptedFileTypes === 'document' ? (
              <File size={18} />
            ) : acceptedFileTypes === 'image' ? (
              <Image size={18} />
            ) : (
              <UploadCloud size={18} />
            )}
            <span>{getButtonText()}</span>
          </>
        )}
      </Button>
    </div>
  );
} 