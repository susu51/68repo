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
      {/* SVG Logo */}
      <svg 
        viewBox="0 0 100 100" 
        className="w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Background Circle with Gradient */}
        <defs>
          <linearGradient id="kuryeciniGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FF6B35" />
            <stop offset="50%" stopColor="#FF8E35" />
            <stop offset="100%" stopColor="#FFB135" />
          </linearGradient>
          <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="2" dy="2" stdDeviation="3" floodColor="#00000020"/>
          </filter>
        </defs>
        
        <circle 
          cx="50" 
          cy="50" 
          r="45" 
          fill="url(#kuryeciniGradient)"
          filter="url(#shadow)"
        />
        
        {/* Delivery Box Icon */}
        <g transform="translate(25, 20)">
          {/* Main Box */}
          <rect x="5" y="15" width="40" height="25" fill="white" rx="3" />
          <rect x="7" y="17" width="36" height="21" fill="#FF6B35" rx="2" />
          
          {/* Box Lines */}
          <line x1="25" y1="15" x2="25" y2="40" stroke="white" strokeWidth="2" />
          <line x1="5" y1="27.5" x2="45" y2="27.5" stroke="white" strokeWidth="1.5" />
          
          {/* Speed Lines */}
          <path d="M 52 20 L 58 20 M 52 25 L 60 25 M 52 30 L 58 30" 
                stroke="white" 
                strokeWidth="2" 
                strokeLinecap="round" />
        </g>
        
        {/* Location Pin */}
        <g transform="translate(60, 55)">
          <circle cx="8" cy="8" r="12" fill="white" />
          <circle cx="8" cy="8" r="8" fill="#FF6B35" />
          <circle cx="8" cy="6" r="3" fill="white" />
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