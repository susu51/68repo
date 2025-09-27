import React, { useState } from 'react';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const FileUpload = ({ label = "Dosya", accept = "image/*", onFileUploaded, required = false }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);

  // Safe label processing
  const safeLabel = label || "Dosya";
  const labelId = `file-input-${safeLabel.replace(/\s+/g, '-').toLowerCase()}`;

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Dosya boyutu çok büyük (max 10MB)');
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        setUploadedFile({
          url: response.data.file_url,
          filename: response.data.original_filename,
          size: response.data.size
        });
        
        onFileUploaded(response.data.file_url);
        toast.success('Dosya başarıyla yüklendi');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Dosya yükleme hatası');
    } finally {
      setUploading(false);
    }
  };

  const removeFile = () => {
    setUploadedFile(null);
    onFileUploaded(null);
  };

  return (
    <div className="space-y-2">
      <Label>{label} {required && <span className="text-red-500">*</span>}</Label>
      
      {!uploadedFile ? (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-gray-400 transition-colors">
          <Input
            type="file"
            accept={accept}
            onChange={handleFileSelect}
            disabled={uploading}
            className="hidden"
            id={`file-input-${label.replace(/\s+/g, '-').toLowerCase()}`}
          />
          <Label
            htmlFor={`file-input-${label.replace(/\s+/g, '-').toLowerCase()}`}
            className="cursor-pointer"
          >
            <div className="flex flex-col items-center space-y-2">
              <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
                📁
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">
                  {uploading ? 'Yükleniyor...' : 'Dosya seç veya sürükle'}
                </p>
                <p className="text-xs text-gray-500">PNG, JPG, PDF (max 10MB)</p>
              </div>
            </div>
          </Label>
        </div>
      ) : (
        <div className="border border-gray-300 rounded-lg p-4 bg-green-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                ✓
              </div>
              <div>
                <p className="text-sm font-medium text-green-800">{uploadedFile.filename}</p>
                <p className="text-xs text-green-600">
                  {(uploadedFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={removeFile}
              className="text-red-600 hover:text-red-700"
            >
              Kaldır
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;