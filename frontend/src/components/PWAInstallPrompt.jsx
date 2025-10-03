/**
 * PWA Installation Prompt Component
 * Encourages users to install Kuryecini as a native app
 */

import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { X, Download, Smartphone, Monitor } from 'lucide-react';
import { analytics } from '../lib/analytics';

export const PWAInstallPrompt = ({ className = '' }) => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Check if running in standalone mode
    const isStandaloneMode = window.matchMedia('(display-mode: standalone)').matches ||
                           window.navigator.standalone ||
                           document.referrer.includes('android-app://');
    
    setIsStandalone(isStandaloneMode);

    // Detect iOS
    const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    setIsIOS(iOS);

    // Handle PWA install prompt
    const handleBeforeInstallPrompt = (e) => {
      console.log('PWA: beforeinstallprompt event fired');
      
      // Prevent Chrome 67 and earlier from automatically showing the prompt
      e.preventDefault();
      
      // Stash the event so it can be triggered later
      setDeferredPrompt(e);
      
      // Check if user has dismissed the prompt recently
      const lastDismissed = localStorage.getItem('pwa-install-dismissed');
      const daysSinceDismissal = lastDismissed ? 
        (Date.now() - parseInt(lastDismissed)) / (1000 * 60 * 60 * 24) : 999;
      
      // Show prompt if not dismissed recently
      if (daysSinceDismissal > 7 && !isStandaloneMode) {
        setShowPrompt(true);
        
        // Track prompt shown
        analytics.custom('pwa_install_prompt_shown', {
          platform: 'android',
          user_agent: navigator.userAgent
        });
      }
    };

    // Listen for install prompt
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // Handle successful app install
    const handleAppInstalled = () => {
      console.log('PWA: App was installed successfully');
      setShowPrompt(false);
      setDeferredPrompt(null);
      
      // Track installation
      analytics.custom('pwa_app_installed', {
        platform: 'android',
        install_source: 'prompt'
      });
    };

    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;

    // Track install button click
    analytics.buttonClick('pwa_install_button', 'install_prompt');

    try {
      // Show the install prompt
      deferredPrompt.prompt();
      
      // Wait for the user to respond to the prompt
      const { outcome } = await deferredPrompt.userChoice;
      
      console.log('PWA: User choice outcome:', outcome);
      
      // Track user choice
      analytics.custom('pwa_install_choice', {
        choice: outcome,
        platform: 'android'
      });
      
      if (outcome === 'accepted') {
        console.log('PWA: User accepted the install prompt');
      } else {
        console.log('PWA: User dismissed the install prompt');
      }
      
    } catch (error) {
      console.error('PWA: Error during install prompt:', error);
    }
    
    // Clear the saved prompt since it can only be used once
    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa-install-dismissed', Date.now().toString());
    
    // Track dismissal
    analytics.custom('pwa_install_prompt_dismissed', {
      platform: isIOS ? 'ios' : 'android'
    });
  };

  // Don't show if already installed or running as standalone
  if (isStandalone) {
    return null;
  }

  // iOS Install Instructions
  if (isIOS && showPrompt) {
    return (
      <Card className={`border-orange-200 bg-orange-50 ${className}`}>
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <Smartphone className="h-6 w-6 text-orange-600 mt-1" />
              <div className="flex-1">
                <h3 className="font-semibold text-orange-900 mb-1">
                  Kuryecini'yi Ana Ekranınıza Ekleyin
                </h3>
                <p className="text-sm text-orange-800 mb-3">
                  Daha hızlı erişim için Kuryecini'yi telefonunuza yükleyin
                </p>
                <ol className="text-sm text-orange-700 space-y-1 mb-4">
                  <li>1. Safari'de paylaş butonuna (↗️) dokunun</li>
                  <li>2. "Ana Ekrana Ekle" seçeneğini bulun</li>
                  <li>3. "Ekle" butonuna dokunun</li>
                </ol>
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleDismiss}
                    className="text-orange-700 border-orange-300 hover:bg-orange-100"
                  >
                    Daha Sonra
                  </Button>
                </div>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDismiss}
              className="text-orange-600 hover:text-orange-800 p-1"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Android/Chrome Install Prompt
  if (showPrompt && deferredPrompt) {
    return (
      <Card className={`border-orange-200 bg-orange-50 ${className}`}>
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <Download className="h-6 w-6 text-orange-600 mt-1" />
              <div className="flex-1">
                <h3 className="font-semibold text-orange-900 mb-1">
                  Kuryecini Uygulamasını İndirin
                </h3>
                <p className="text-sm text-orange-800 mb-3">
                  Daha hızlı sipariş ve bildirimleri kaçırmamak için uygulamayı indirin
                </p>
                <div className="flex flex-wrap gap-2">
                  <Button 
                    onClick={handleInstallClick}
                    size="sm"
                    className="bg-orange-600 hover:bg-orange-700 text-white"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Uygulamayı İndir
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleDismiss}
                    className="text-orange-700 border-orange-300 hover:bg-orange-100"
                  >
                    Daha Sonra
                  </Button>
                </div>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDismiss}
              className="text-orange-600 hover:text-orange-800 p-1"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return null;
};

// PWA Status Indicator Component
export const PWAStatus = () => {
  const [isPWA, setIsPWA] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    // Check if running as PWA
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                        window.navigator.standalone ||
                        document.referrer.includes('android-app://');
    
    setIsPWA(isStandalone);

    // Online/offline status
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!isPWA) return null;

  return (
    <div className="fixed top-4 right-4 z-50">
      <div className={`px-3 py-1 rounded-full text-xs font-medium ${
        isOnline 
          ? 'bg-green-100 text-green-800 border border-green-200' 
          : 'bg-red-100 text-red-800 border border-red-200'
      }`}>
        {isOnline ? '🟢 Çevrimiçi' : '🔴 Çevrimdışı'}
      </div>
    </div>
  );
};

// PWA Update Available Component
export const PWAUpdatePrompt = () => {
  const [showUpdatePrompt, setShowUpdatePrompt] = useState(false);
  const [waitingWorker, setWaitingWorker] = useState(null);

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        window.location.reload();
      });

      // Check for updates
      navigator.serviceWorker.ready.then((registration) => {
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                setWaitingWorker(newWorker);
                setShowUpdatePrompt(true);
                
                // Track update available
                analytics.custom('pwa_update_available');
              }
            });
          }
        });
      });
    }
  }, []);

  const handleUpdate = () => {
    if (waitingWorker) {
      waitingWorker.postMessage({ type: 'SKIP_WAITING' });
      setShowUpdatePrompt(false);
      
      // Track update accepted
      analytics.custom('pwa_update_accepted');
    }
  };

  const handleDismiss = () => {
    setShowUpdatePrompt(false);
    
    // Track update dismissed
    analytics.custom('pwa_update_dismissed');
  };

  if (!showUpdatePrompt) return null;

  return (
    <Card className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 border-blue-200 bg-blue-50">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <Monitor className="h-6 w-6 text-blue-600 mt-1" />
            <div className="flex-1">
              <h3 className="font-semibold text-blue-900 mb-1">
                Güncelleme Mevcut
              </h3>
              <p className="text-sm text-blue-800 mb-3">
                Yeni özellikler ve iyileştirmeler hazır. Güncellemek ister misiniz?
              </p>
              <div className="flex space-x-2">
                <Button 
                  onClick={handleUpdate}
                  size="sm"
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Güncelle
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleDismiss}
                  className="text-blue-700 border-blue-300 hover:bg-blue-100"
                >
                  Daha Sonra
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PWAInstallPrompt;