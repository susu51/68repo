import React from 'react';
import { Card, CardContent } from './card';

// Loading Spinner Component
export const LoadingSpinner = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8', 
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  return (
    <div className={`animate-spin rounded-full border-2 border-gray-300 border-t-orange-500 ${sizeClasses[size]} ${className}`}></div>
  );
};

// Loading Card for Lists
export const LoadingCard = ({ count = 3, className = '' }) => {
  return (
    <div className={`space-y-4 ${className}`}>
      {[...Array(count)].map((_, index) => (
        <Card key={index} className="animate-pulse">
          <CardContent className="p-4">
            <div className="flex space-x-4">
              <div className="rounded-lg bg-gray-300 h-16 w-16"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-300 rounded w-3/4"></div>
                <div className="h-3 bg-gray-300 rounded w-1/2"></div>
                <div className="h-3 bg-gray-300 rounded w-1/4"></div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

// Loading Screen for Full Page
export const LoadingScreen = ({ message = 'Yükleniyor...', icon = '⏳' }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
      <LoadingSpinner size="xl" className="mb-4" />
      <h3 className="text-lg font-semibold text-gray-700 mb-2">
        {icon} {message}
      </h3>
      <p className="text-gray-500 text-center max-w-md">
        Veriler yükleniyor, lütfen bekleyin...
      </p>
    </div>
  );
};

// Loading List Item
export const LoadingListItem = () => {
  return (
    <div className="animate-pulse flex items-center space-x-4 p-4 border-b">
      <div className="rounded-full bg-gray-300 h-10 w-10"></div>
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-gray-300 rounded w-3/4"></div>
        <div className="h-3 bg-gray-300 rounded w-1/2"></div>
      </div>
    </div>
  );
};

export default LoadingSpinner;