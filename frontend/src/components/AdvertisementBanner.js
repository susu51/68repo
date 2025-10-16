import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/http';

const AdvertisementBanner = ({ userCity }) => {
  const [advertisements, setAdvertisements] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAdvertisements();
  }, [userCity]);

  const fetchAdvertisements = async () => {
    try {
      const cityParam = userCity ? `?city=${encodeURIComponent(userCity)}` : '';
      const response = await api(`/advertisements/active${cityParam}`);
      const data = await response.json();
      
      if (data.success && data.advertisements.length > 0) {
        setAdvertisements(data.advertisements);
      }
    } catch (error) {
      console.error('Error fetching advertisements:', error);
    } finally {
      setLoading(false);
    }
  };

  // Auto-advance slider every 7 seconds
  useEffect(() => {
    if (advertisements.length <= 1 || isHovered) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % advertisements.length);
    }, 7000);

    return () => clearInterval(interval);
  }, [advertisements.length, isHovered]);

  const goToSlide = useCallback((index) => {
    setCurrentIndex(index);
  }, []);

  const goToPrevious = useCallback(() => {
    setCurrentIndex((prev) => (prev - 1 + advertisements.length) % advertisements.length);
  }, [advertisements.length]);

  const goToNext = useCallback(() => {
    setCurrentIndex((prev) => (prev + 1) % advertisements.length);
  }, [advertisements.length]);

  const handleAdClick = (ad) => {
    // Navigate to restaurant menu page
    window.location.href = `/#/customer/restaurant/${ad.business_id}`;
  };

  if (loading) {
    return (
      <div className="w-full h-48 bg-gray-100 rounded-lg animate-pulse"></div>
    );
  }

  if (advertisements.length === 0) {
    return null; // Don't show anything if no advertisements
  }

  const currentAd = advertisements[currentIndex];

  return (
    <div 
      className="relative w-full h-48 sm:h-56 md:h-64 lg:h-80 rounded-lg overflow-hidden shadow-lg mb-4 sm:mb-6"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Banner Image */}
      <div 
        className="w-full h-full cursor-pointer transition-transform duration-300 hover:scale-105"
        onClick={() => handleAdClick(currentAd)}
      >
        <img
          src={`${process.env.REACT_APP_BACKEND_URL || ''}${currentAd.image_url}`}
          alt={currentAd.title || currentAd.business_name}
          className="w-full h-full object-cover"
        />
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent"></div>
        
        {/* Content Overlay */}
        <div className="absolute bottom-0 left-0 right-0 p-3 sm:p-4 md:p-6 text-white">
          <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-bold mb-1 sm:mb-2 line-clamp-1">{currentAd.business_name}</h3>
          {currentAd.title && (
            <p className="text-xs sm:text-base md:text-lg lg:text-xl mb-1 sm:mb-2 line-clamp-1">{currentAd.title}</p>
          )}
          <div className="flex items-center gap-1 sm:gap-2 text-[10px] sm:text-xs md:text-sm flex-wrap">
            <span className="bg-orange-600 px-2 sm:px-3 py-0.5 sm:py-1 rounded-full whitespace-nowrap">📍 {currentAd.city}</span>
            <span className="bg-white/20 px-2 sm:px-3 py-0.5 sm:py-1 rounded-full whitespace-nowrap">Tıkla & Sipariş Ver</span>
          </div>
        </div>
      </div>

      {/* Navigation Arrows */}
      {advertisements.length > 1 && (
        <>
          <button
            onClick={goToPrevious}
            className="absolute left-2 sm:left-4 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-gray-800 rounded-full w-8 h-8 sm:w-10 sm:h-10 flex items-center justify-center shadow-lg transition-all hover:scale-110 text-lg sm:text-xl"
            aria-label="Previous"
          >
            ‹
          </button>
          <button
            onClick={goToNext}
            className="absolute right-2 sm:right-4 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-gray-800 rounded-full w-8 h-8 sm:w-10 sm:h-10 flex items-center justify-center shadow-lg transition-all hover:scale-110 text-lg sm:text-xl"
            aria-label="Next"
          >
            ›
          </button>
        </>
      )}

      {/* Dots Indicator */}
      {advertisements.length > 1 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex space-x-2">
          {advertisements.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`rounded-full transition-all ${
                index === currentIndex
                  ? 'bg-orange-600 w-8 h-2'
                  : 'bg-white/60 hover:bg-white/80 w-2 h-2'
              }`}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      )}

      {/* Slide Counter */}
      {advertisements.length > 1 && (
        <div className="absolute top-4 right-4 bg-black/50 text-white px-3 py-1 rounded-full text-sm">
          {currentIndex + 1} / {advertisements.length}
        </div>
      )}
    </div>
  );
};

export default AdvertisementBanner;
