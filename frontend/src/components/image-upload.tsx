"use client"

import React, { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { ImagePlus, X, FileImage, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { uploadImages } from "@/lib/api";
import { toast } from "sonner";

interface ImageUploadProps {
  onImagesUploaded: (imageData: any[]) => void;
  className?: string;
}

export function ImageUpload({ onImagesUploaded, className }: ImageUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [previewImages, setPreviewImages] = useState<{ url: string; file: File }[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    
    // Create previews for selected images
    const newPreviews = files.map(file => ({
      url: URL.createObjectURL(file),
      file
    }));
    
    setPreviewImages(prev => [...prev, ...newPreviews]);
    
    // Clear file input so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };
  
  const removeImage = (index: number) => {
    setPreviewImages(prev => {
      const newPreviews = [...prev];
      // Revoke the object URL to prevent memory leaks
      URL.revokeObjectURL(newPreviews[index].url);
      newPreviews.splice(index, 1);
      return newPreviews;
    });
  };
  
  const handleUpload = async () => {
    if (previewImages.length === 0) return;
    
    try {
      setIsUploading(true);
      
      // Get all files to upload
      const files = previewImages.map(preview => preview.file);
      
      // Upload the images
      const result = await uploadImages(files);
      
      // Pass the uploaded image data back to the parent component
      onImagesUploaded(result.images);
      
      // Clear previews after successful upload
      previewImages.forEach(preview => URL.revokeObjectURL(preview.url));
      setPreviewImages([]);
      
      toast.success(`${files.length} image(s) uploaded successfully`);
    } catch (error) {
      console.error('Error uploading images:', error);
      toast.error('Failed to upload images');
    } finally {
      setIsUploading(false);
    }
  };
  
  return (
    <div className={cn("space-y-2", className)}>
      {/* Image previews */}
      {previewImages.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {previewImages.map((preview, index) => (
            <div key={index} className="relative w-20 h-20">
              <img 
                src={preview.url} 
                alt={`Preview ${index}`} 
                className="w-20 h-20 object-cover rounded-md border" 
              />
              <button
                type="button"
                onClick={() => removeImage(index)}
                className="absolute -top-2 -right-2 bg-destructive text-white rounded-full p-1"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
      
      <div className="flex gap-2">
        {/* Hidden file input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          accept="image/*"
          multiple
        />
        
        {/* Select image button */}
        <Button
          type="button"
          variant="outline"
          size="icon"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
        >
          <FileImage size={16} />
        </Button>
        
        {/* Upload button - only show if images are selected */}
        {previewImages.length > 0 && (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleUpload}
            disabled={isUploading}
          >
            {isUploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <ImagePlus className="mr-2 h-4 w-4" />
                Send {previewImages.length} image{previewImages.length !== 1 ? 's' : ''}
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
} 