# Multimodal Implementation Guide

This document provides a detailed explanation of how multimodal capabilities (text + images) are implemented in the Chat Application.

## Overview

The multimodal implementation allows users to:

1. Upload images to the chat
2. Send messages with both text and images
3. Receive AI responses about the image content
4. Have meaningful conversations about visual content

## System Components

The multimodal implementation consists of the following components:

### Backend Components

1. **Upload Service**: Processes and stores uploaded images
2. **ChatService with Multimodal Support**: Detects models that support multimodal inputs
3. **Message Converter**: Transforms multimodal messages into model-specific formats

### Frontend Components

1. **ImageUpload Component**: UI for uploading and previewing images
2. **ChatMessage Component**: Displays multimodal messages in the conversation
3. **API Client**: Handles communication with the backend for image uploads

## Data Flow

The typical flow for multimodal interaction is:

1. User selects an image through the UI
2. Image is uploaded to the server via API
3. Server processes the image (validation, resizing if needed)
4. Server returns image data with URL
5. Frontend includes image URL in the message object
6. Message with both text and image is sent to the AI model
7. AI processes the multimodal input and responds
8. Response is displayed to the user

## Implementation Details

### 1. Backend Image Processing (upload.py)

```python
@router.post("/images")
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload images to be used in chat
    
    Returns image URLs that can be used in multimodal chat messages
    """
    result = []
    
    try:
        for file in files:
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            # Read and validate image
            contents = await file.read()
            try:
                img = Image.open(BytesIO(contents))
                img.verify()  # Verify it's a valid image
                
                # Optional: resize large images to save bandwidth
                img = Image.open(BytesIO(contents))
                if max(img.size) > 1024:  # If larger than 1024px in any dimension
                    img.thumbnail((1024, 1024), Image.LANCZOS)
                    buffer = BytesIO()
                    img.save(buffer, format=img.format or "JPEG")
                    contents = buffer.getvalue()
            except Exception as e:
                logger.error(f"Invalid image file: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid image file: {file.filename}")
            
            # Save the file
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # For simplicity, encode as base64 for direct use in messages
            base64_image = base64.b64encode(contents).decode("utf-8")
            mime_type = file.content_type or "image/jpeg"
            data_url = f"data:{mime_type};base64,{base64_image}"
            
            # Add results with both local path and base64 data URL
            result.append({
                "filename": file.filename,
                "content_type": mime_type,
                "size": len(contents),
                "image_url": data_url,
                "file_path": f"/uploads/{unique_filename}"
            })
        
        return {"images": result}
    
    except Exception as e:
        logger.error(f"Error uploading images: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading images: {str(e)}")
```

### 2. Multimodal Support Detection (chat_service.py)

```python
def _check_multimodal_support(self, model: str) -> bool:
    """Check if the model supports multimodal content (images)"""
    # Get multimodal supported models from environment variables
    vision_models = os.getenv("MULTIMODAL_OPENAI_MODELS", "").split(",")
    gemini_vision_models = os.getenv("MULTIMODAL_GOOGLE_MODELS", "").split(",")
    nvidia_vision_models = os.getenv("MULTIMODAL_NVIDIA_MODELS", "").split(",")
    
    # Clean whitespace
    vision_models = [m.strip() for m in vision_models if m.strip()]
    gemini_vision_models = [m.strip() for m in gemini_vision_models if m.strip()]
    nvidia_vision_models = [m.strip() for m in nvidia_vision_models if m.strip()]
    
    # Check if model is in any multimodal support list
    if (model in vision_models or 
        model in gemini_vision_models or 
        model in nvidia_vision_models):
        return True
    
    # Also check for specific model prefixes
    if (model.startswith("gpt-4-vision") or 
        model.startswith("gpt-4o") or 
        model.startswith("gemini") or 
        "vision" in model.lower()):
        return True
        
    return False
```

### 3. Multimodal Message Conversion (chat_service.py)

```python
def _convert_to_langchain_messages(self, messages: List[Dict[str, Any]]) -> List[Union[HumanMessage, AIMessage, SystemMessage]]:
    """Convert chat messages to LangChain message format"""
    langchain_messages = []
    
    for message in messages:
        role = message.get("role", "")
        content = message.get("content", "")
        
        # Handle multimodal content (can be string or list of content parts)
        if isinstance(content, list):
            # For multimodal content, process each part
            processed_content = []
            
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        # Text content
                        processed_content.append({"type": "text", "text": part.get("text", "")})
                    elif part.get("type") == "image":
                        # Image content
                        image_url = part.get("image_url", {}).get("url", "")
                        if image_url:
                            processed_content.append({
                                "type": "image_url", 
                                "image_url": {"url": image_url}
                            })
            
            if role == "user":
                langchain_messages.append(HumanMessage(content=processed_content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=processed_content))
            elif role == "system":
                # For system messages, convert multimodal to text as most models expect
                # text-only system messages
                text_parts = [part.get("text", "") for part in processed_content 
                             if part.get("type") == "text"]
                langchain_messages.append(SystemMessage(content=" ".join(text_parts)))
        else:
            # Regular text content (string)
            if role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            elif role == "system":
                langchain_messages.append(SystemMessage(content=content))
    
    return langchain_messages
```

### 4. Frontend Image Upload Component (image-upload.tsx)

```typescript
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
  
  // ... render UI ...
}
```

### 5. Frontend API Client (api.ts)

```typescript
export async function uploadImages(files: File[]): Promise<any> {
  const formData = new FormData();
  
  // Append each file to the FormData
  files.forEach(file => {
    formData.append('files', file);
  });
  
  try {
    const response = await fetch('/api/upload/images', {
      method: 'POST',
      body: formData,
      // No need to set content-type header, fetch will set it with the correct boundary
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error uploading images:', error);
    throw error;
  }
}
```

### 6. Frontend Chat Message Handling (page.tsx)

```typescript
// Handle message submission
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  if (!input.trim() && pendingImages.length === 0) return;
  
  // Ensure a model is selected
  if (!selectedModel) {
    toast.error('Please select a model');
    return;
  }
  
  setError('');
  setIsLoading(true);
  
  // Prepare user message content
  let userMessageContent: any = input;
  
  // If we have images, create multimodal content
  if (pendingImages.length > 0) {
    userMessageContent = [
      { type: "text", text: input || "Check out this image:" },
      ...pendingImages.map(img => ({
        type: "image",
        image_url: { url: img.image_url }
      }))
    ];
  }
  
  // Create new user message
  const userMessage = { role: 'user', content: userMessageContent };
  
  // Update the UI immediately with user message
  const updatedMessages = [...messages, userMessage];
  setMessages(updatedMessages);
  setInput('');
  setPendingImages([]); // Clear pending images
  setShowImageUpload(false); // Hide image upload UI
  
  // ... process API request and handle response ...
}
```

### 7. Frontend ChatMessage Component (chat-message.tsx)

```typescript
// Process message content which could be string or array of content parts
useEffect(() => {
  if (typeof message.content === 'string') {
    // Simple text content
    setDisplayedContent(message.content);
  } else if (Array.isArray(message.content)) {
    // Multimodal content - render as React nodes
    const contentParts = message.content.map((part, index) => {
      if (part.type === 'text' && part.text) {
        return (
          <div key={`text-${index}`} className="prose prose-sm dark:prose-invert">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {part.text}
            </ReactMarkdown>
          </div>
        );
      } else if (part.type === 'image_url' && part.image_url) {
        return (
          <div key={`image-${index}`} className="my-2">
            <img 
              src={part.image_url.url} 
              alt="Image in conversation" 
              className="max-w-full max-h-[300px] rounded-md object-contain"
            />
          </div>
        );
      }
      return null;
    });
    
    setDisplayedContent(<>{contentParts}</>);
  }
}, [message.content, message.streaming]);
```

## Message Format

The multimodal message format follows this structure:

```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "What's in this image?"
    },
    {
      "type": "image",
      "image_url": {
        "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."
      }
    }
  ]
}
```

## Provider-Specific Considerations

Different AI providers handle multimodal inputs with different requirements:

### OpenAI (GPT-4 Vision, GPT-4o)

- Supports "image_url" format with both URLs and base64-encoded images
- Maximum of 20 images per request (practical limit)
- Base64 images should include MIME type prefix

### Google (Gemini)

- Supports both inline base64 and URL images
- Uses "inline_data" or "file_data" format internally
- May have different limits on image sizes and counts

### NVIDIA (LLaVA)

- Support varies by specific model
- May need special handling for image formats
- Image size and resolution limitations may apply

## Best Practices

1. **Resize Images**: Always resize large images before sending to models
2. **Base64 Encoding**: Use base64 encoding for direct embedding in messages
3. **Image Validation**: Verify images are valid before processing
4. **Error Handling**: Provide graceful degradation when image processing fails
5. **Provider Selection**: Ensure the selected model supports multimodal inputs

## Troubleshooting

### Common Issues

1. **"Model doesn't support image inputs"**: Ensure the selected model is in the multimodal configuration list
2. **Image too large**: Implement automatic resizing for large images 
3. **Invalid image format**: Validate image formats and provide user feedback
4. **API errors with multimodal content**: Check the specific error message and provider documentation

### Debugging Tips

1. Log the full message structure before sending to the API
2. Verify the image data URL format is correct
3. Check for missing or malformed content types
4. Test with a known working model like GPT-4o or Gemini Pro

## Future Improvements

Potential enhancements to the multimodal implementation:

1. **Video Support**: Add support for short video clips
2. **Document Analysis**: Enhanced processing for document images
3. **Advanced Image Processing**: Pre-processing for better model results
4. **Image Annotations**: Allow users to annotate images before sending
5. **Multiple Model Support**: Allow sending different parts of multimodal messages to specialized models

## References

- [OpenAI Vision API Documentation](https://platform.openai.com/docs/guides/vision)
- [Google Gemini Multimodal Documentation](https://ai.google.dev/gemini-api/docs/get-started/multimodal)
- [LangChain Multimodal Documentation](https://js.langchain.com/docs/modules/model_io/models/chat/how_to/multimodal) 