import React from 'react';
import { Button } from './button';
import { Card, CardContent } from './card';
import { AlertTriangle, Wifi, Server, RefreshCw } from 'lucide-react';

// Generic Error State Component
export const ErrorState = ({ 
  icon = <AlertTriangle className="w-12 h-12 text-red-500" />, 
  title = 'Bir Hata Oluştu', 
  description = 'Beklenmedik bir hata meydana geldi.',
  actionText = 'Tekrar Dene',
  onAction = null,
  className = '',
  variant = 'default' // 'default', 'network', 'server', 'notfound'
}) => {
  const variants = {
    network: {
      icon: <Wifi className="w-12 h-12 text-orange-500" />,
      title: 'Bağlantı Hatası',
      description: 'İnternet bağlantınızı kontrol edip tekrar deneyin.'
    },
    server: {
      icon: <Server className="w-12 h-12 text-red-500" />,
      title: 'Sunucu Hatası',
      description: 'Sunucu geçici olarak kullanılamıyor. Lütfen daha sonra tekrar deneyin.'
    },
    notfound: {
      icon: <span className="text-6xl">🔍</span>,
      title: 'Sayfa Bulunamadı',
      description: 'Aradığınız sayfa mevcut değil veya taşınmış olabilir.'
    }
  };

  const currentVariant = variants[variant] || { icon, title, description };

  return (
    <div className={`flex flex-col items-center justify-center min-h-[300px] p-8 text-center ${className}`}>
      <div className="mb-4">{currentVariant.icon}</div>
      <h3 className="text-lg font-semibold text-gray-700 mb-2">{currentVariant.title}</h3>
      <p className="text-gray-500 mb-6 max-w-md">{currentVariant.description}</p>
      
      {actionText && onAction && (
        <Button 
          onClick={onAction}
          className="bg-red-500 hover:bg-red-600 text-white"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          {actionText}
        </Button>
      )}
    </div>
  );
};

// Network Error
export const NetworkError = ({ onRetry }) => {
  return (
    <ErrorState
      variant="network"
      onAction={onRetry}
    />
  );
};

// Server Error
export const ServerError = ({ onRetry }) => {
  return (
    <ErrorState
      variant="server"
      onAction={onRetry}
    />
  );
};

// API Error Handler Component
export const APIErrorBanner = ({ error, onDismiss, className = '' }) => {
  const getErrorMessage = (error) => {
    if (error?.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error?.response?.status) {
      const statusMessages = {
        400: 'Geçersiz istek. Lütfen bilgilerinizi kontrol edin.',
        401: 'Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.',
        403: 'Bu işlem için yetkiniz bulunmuyor.',
        404: 'İstenen kaynak bulunamadı.',
        500: 'Sunucu hatası. Lütfen daha sonra tekrar deneyin.',
        503: 'Servis geçici olarak kullanılamıyor.'
      };
      return statusMessages[error.response.status] || 'Beklenmedik bir hata oluştu.';
    }
    return error?.message || 'Bilinmeyen bir hata oluştu.';
  };

  const getErrorIcon = (error) => {
    if (error?.code === 'NETWORK_ERROR') return '📡';
    if (error?.response?.status >= 500) return '🔧';
    if (error?.response?.status === 401) return '🔒';
    if (error?.response?.status === 403) return '⛔';
    return '⚠️';
  };

  return (
    <Card className={`border-red-200 bg-red-50 ${className}`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-xl">{getErrorIcon(error)}</span>
            <div>
              <h4 className="font-semibold text-red-800">Hata</h4>
              <p className="text-red-700 text-sm">{getErrorMessage(error)}</p>
            </div>
          </div>
          {onDismiss && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onDismiss}
              className="text-red-600 hover:text-red-800"
            >
              ✕
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Toast Error Handler
export const showErrorToast = (error, toast) => {
  const message = error?.response?.data?.detail || error?.message || 'Beklenmedik bir hata oluştu';
  
  toast.error(message, {
    duration: 4000,
    position: 'top-center',
    style: {
      background: '#FEE2E2',
      border: '1px solid #FECACA',
      color: '#991B1B',
    },
    icon: '⚠️',
  });
};

export default ErrorState;