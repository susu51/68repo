import React from 'react';

export const KuryeciniLogo = ({ size = 'medium', className = '' }) => {
  const sizeClasses = {
    small: 'w-8 h-8',
    medium: 'w-12 h-12', 
    large: 'w-20 h-20',
    xl: 'w-32 h-32'
  };

  return (
    <div className={`${sizeClasses[size]} ${className} relative`}>
      {/* Modern Kuryecini Logo */}
      <svg 
        viewBox="0 0 120 120" 
        className="w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Main Orange Gradient */}
          <linearGradient id="kuryeciniMain" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FF6B35" />
            <stop offset="50%" stopColor="#E84A5F" />
            <stop offset="100%" stopColor="#C73E1D" />
          </linearGradient>
          
          {/* Accent Gradient */}
          <linearGradient id="kuryeciniAccent" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFD700" />
            <stop offset="100%" stopColor="#FFA500" />
          </linearGradient>
          
          {/* Shadow Filter */}
          <filter id="logoShadow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="4" stdDeviation="4" floodColor="#00000025"/>
          </filter>
        </defs>
        
        {/* Background Circle */}
        <circle 
          cx="60" 
          cy="60" 
          r="55" 
          fill="url(#kuryeciniMain)"
          filter="url(#logoShadow)"
        />
        
        {/* Inner Design Elements */}
        <g transform="translate(60, 60)">
          {/* Delivery Motorcycle/Scooter Silhouette */}
          <g transform="translate(-35, -25)">
            {/* Main Body */}
            <path d="M15 20 Q25 15 35 18 Q45 20 55 25 L52 35 Q45 40 35 38 Q25 35 15 30 Z" 
                  fill="white" 
                  fillOpacity="0.9"/>
            
            {/* Front Wheel */}
            <circle cx="20" cy="35" r="8" fill="url(#kuryeciniAccent)" />
            <circle cx="20" cy="35" r="5" fill="white" />
            
            {/* Back Wheel */}
            <circle cx="50" cy="35" r="8" fill="url(#kuryeciniAccent)" />
            <circle cx="50" cy="35" r="5" fill="white" />
            
            {/* Delivery Box */}
            <rect x="30" y="10" width="16" height="12" rx="2" fill="white" />
            <rect x="32" y="12" width="12" height="8" rx="1" fill="url(#kuryeciniAccent)" />
            
            {/* Speed Lines */}
            <g opacity="0.7">
              <line x1="60" y1="15" x2="68" y2="15" stroke="white" strokeWidth="2" strokeLinecap="round" />
              <line x1="62" y1="20" x2="70" y2="20" stroke="white" strokeWidth="2" strokeLinecap="round" />
              <line x1="60" y1="25" x2="68" y2="25" stroke="white" strokeWidth="2" strokeLinecap="round" />
            </g>
          </g>
          
          {/* Stylized "K" Letter */}
          <g transform="translate(-12, -15)">
            <path d="M2 0 L8 0 L8 12 L18 0 L26 0 L16 12 L26 30 L18 30 L8 18 L8 30 L2 30 Z" 
                  fill="white" 
                  fontWeight="bold"/>
          </g>
        </g>
      </svg>
    </div>
  );
};

export const KuryeciniTextLogo = ({ size = 'medium', className = '' }) => {
  const sizeClasses = {
    small: 'text-lg',
    medium: 'text-2xl',
    large: 'text-4xl',
    xl: 'text-6xl'
  };

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      <KuryeciniLogo size={size === 'xl' ? 'large' : size === 'large' ? 'medium' : 'small'} />
      <div className="flex flex-col">
        <span className={`font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent ${sizeClasses[size]}`}>
          Kuryecini
        </span>
        {(size === 'large' || size === 'xl') && (
          <span className="text-sm text-gray-500 -mt-1">
            Türkiye'nin En Hızlı Teslimat Platformu
          </span>
        )}
      </div>
    </div>
  );
};

export const KuryeciniIcon = ({ className = '' }) => {
  return (
    <span className={`text-2xl ${className}`}>🚀</span>
  );
};

export default KuryeciniLogo;