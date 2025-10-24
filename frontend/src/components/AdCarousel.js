import React, { useState, useEffect } from 'react';
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AdCarousel = ({ city = null, category = null }) => {
  const [ads, setAds] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [loading, setLoading] = useState(true);

  // Fetch ads from backend
  useEffect(() => {
    const fetchAds = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API}/ads/active`, {
          params: { city, category }
        });
        
        const activeAds = response.data || [];
        setAds(activeAds);
        
        if (activeAds.length === 0) {
          // Set default/demo ads if no ads available
          setAds(getDefaultAds());
        }
      } catch (error) {
        console.error('Failed to fetch ads:', error);
        setAds(getDefaultAds());
      }
      setLoading(false);
    };

    fetchAds();
  }, [city, category]);

  // Auto-scroll functionality
  useEffect(() => {
    if (!isPlaying || ads.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => 
        prevIndex === ads.length - 1 ? 0 : prevIndex + 1
      );
    }, 4000); // 4 seconds auto-scroll

    return () => clearInterval(interval);
  }, [ads.length, isPlaying]);

  // Handle manual navigation
  const goToSlide = (index) => {
    setCurrentIndex(index);
  };

  const goNext = () => {
    setCurrentIndex(currentIndex === ads.length - 1 ? 0 : currentIndex + 1);
  };

  const goPrevious = () => {
    setCurrentIndex(currentIndex === 0 ? ads.length - 1 : currentIndex - 1);
  };

  // Handle ad click
  const handleAdClick = async (ad) => {
    try {
      // Track click
      await axios.post(`${API}/ads/${ad.id}/click`);
      
      // Open target URL
      if (ad.targetUrl) {
        window.open(ad.targetUrl, '_blank');
      }
    } catch (error) {
      console.error('Failed to track ad click:', error);
    }
  };

  // Track impression
  useEffect(() => {
    if (ads.length > 0 && currentIndex < ads.length) {
      const currentAd = ads[currentIndex];
      if (currentAd.id) {
        // Track impression
        axios.post(`${API}/ads/${currentAd.id}/impression`).catch(err => {
          console.error('Failed to track impression:', err);
        });
      }
    }
  }, [currentIndex, ads]);

  if (loading) {
    return (
      <div className="w-full h-48 bg-gradient-to-r from-gray-200 to-gray-300 rounded-xl animate-pulse flex items-center justify-center">
        <div className="text-gray-500">Reklamlar yükleniyor...</div>
      </div>
    );
  }

  if (ads.length === 0) {
    return null;
  }

  const currentAd = ads[currentIndex];

  return (
    <div className="relative w-full group">
      {/* Main Ad Display */}
      <Card 
        className="overflow-hidden cursor-pointer hover:shadow-xl transition-all duration-300 transform hover:scale-[1.02]"
        onClick={() => handleAdClick(currentAd)}
      >
        <CardContent className="p-0 relative">
          {/* Background Image */}
          <div 
            className="h-48 bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-center relative overflow-hidden"
            style={{
              backgroundImage: currentAd.imgUrl ? `url(${currentAd.imgUrl})` : undefined,
              backgroundSize: 'cover',
              backgroundPosition: 'center'
            }}
          >
            {/* Overlay for better text readability */}
            <div className="absolute inset-0 bg-black/30"></div>
            
            {/* Ad Content */}
            <div className="relative z-10 text-center text-white px-6">
              <h3 className="text-2xl font-bold mb-2 drop-shadow-lg">
                {currentAd.title || '🎉 Kuryecini ile Hızlı Teslimat!'}
              </h3>
              <p className="text-lg opacity-90 drop-shadow-md">
                {currentAd.description || 'Binlerce restoran, tek tıkla kapınızda!'}
              </p>
              
              {/* Call to Action */}
              <Button 
                className="mt-4 bg-white text-orange-600 hover:bg-gray-100 font-semibold"
                onClick={(e) => {
                  e.stopPropagation();
                  handleAdClick(currentAd);
                }}
              >
                {currentAd.ctaText || 'Hemen Keşfet'} →
              </Button>
            </div>

            {/* Play/Pause Control */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsPlaying(!isPlaying);
              }}
              className="absolute top-4 right-4 bg-black/30 hover:bg-black/50 text-white p-2 rounded-full transition-all duration-200"
            >
              {isPlaying ? '⏸️' : '▶️'}
            </button>

            {/* Ad Type Badge */}
            {currentAd.type && (
              <Badge 
                variant="secondary" 
                className="absolute top-4 left-4 bg-white/20 text-white backdrop-blur-sm"
              >
                {currentAd.type}
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Navigation Controls (visible on hover) */}
      {ads.length > 1 && (
        <>
          {/* Previous/Next Buttons */}
          <button
            onClick={goPrevious}
            className="absolute left-2 top-1/2 transform -translate-y-1/2 bg-black/30 hover:bg-black/50 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-200"
          >
            ◀
          </button>
          <button
            onClick={goNext}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-black/30 hover:bg-black/50 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-200"
          >
            ▶
          </button>

          {/* Dots Indicator */}
          <div className="flex justify-center space-x-2 mt-4">
            {ads.map((_, index) => (
              <button
                key={index}
                onClick={() => goToSlide(index)}
                className={`w-3 h-3 rounded-full transition-all duration-200 ${
                  index === currentIndex 
                    ? 'bg-orange-600 w-8' 
                    : 'bg-gray-300 hover:bg-gray-400'
                }`}
              />
            ))}
          </div>
        </>
      )}

      {/* Ad Counter */}
      {ads.length > 1 && (
        <div className="absolute bottom-4 right-4 bg-black/30 text-white px-2 py-1 rounded text-sm backdrop-blur-sm">
          {currentIndex + 1} / {ads.length}
        </div>
      )}
    </div>
  );
};

// Default/Demo ads for when no ads are available
const getDefaultAds = () => [
  {
    id: 'demo-1',
    title: '🎉 Kuryecini ile Hızlı Teslimat!',
    description: 'Binlerce restoran, tek tıkla kapınızda!',
    ctaText: 'Hemen Sipariş Ver',
    type: 'Platform',
    imgUrl: null,
    targetUrl: null
  },
  {
    id: 'demo-2', 
    title: '🍕 En Sevilen Restoranlar',
    description: 'Favori yemekleriniz 15 dakikada kapınızda!',
    ctaText: 'Keşfet',
    type: 'Restaurant',
    imgUrl: null,
    targetUrl: null
  },
  {
    id: 'demo-3',
    title: '⚡ Ücretsiz Teslimat',
    description: '50₺ ve üzeri siparişlerde kargo bedava!',
    ctaText: 'Fırsatı Yakala',
    type: 'Campaign',
    imgUrl: null,
    targetUrl: null
  }
];

export default AdCarousel;