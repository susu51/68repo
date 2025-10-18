import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/card';

const MaintenancePage = () => {
  const [maintenanceData, setMaintenanceData] = useState({
    message: 'Sistemimiz bakımda. Kısa süre içinde tekrar hizmetinizdeyiz!',
    eta: null,
    contact_email: 'destek@kuryecini.com',
    contact_phone: '+90 555 123 45 67'
  });

  useEffect(() => {
    // Fetch maintenance status
    fetch('/api/maintenance-status')
      .then(res => res.json())
      .then(data => {
        if (data.message) {
          setMaintenanceData(prev => ({
            ...prev,
            message: data.message,
            eta: data.eta
          }));
        }
      })
      .catch(err => console.error('Error fetching maintenance status:', err));
  }, []);

  // Kurye görselleri
  const kuryeImages = [
    'https://customer-assets.emergentagent.com/job_delivery-nexus-5/artifacts/yt8a3xfb_1760691967744.jpg',
    'https://customer-assets.emergentagent.com/job_delivery-nexus-5/artifacts/paqce04r_1760692093757.jpg',
    'https://customer-assets.emergentagent.com/job_delivery-nexus-5/artifacts/s8d64v73_1760692232542.jpg',
    'https://customer-assets.emergentagent.com/job_delivery-nexus-5/artifacts/xm78shmz_1760694524665.jpg'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-orange-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-orange-100">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-orange-600 rounded-full flex items-center justify-center">
              <span className="text-2xl">🚀</span>
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-orange-500 bg-clip-text text-transparent">
              Kuryecini
            </h1>
          </div>
          <div className="flex items-center space-x-2">
            <div className="animate-pulse flex items-center space-x-2 bg-orange-100 px-4 py-2 rounded-full">
              <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
              <span className="text-sm font-medium text-orange-700">Bakımda</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="inline-block mb-6">
            <div className="relative">
              <div className="absolute inset-0 bg-orange-500 blur-3xl opacity-20"></div>
              <div className="relative bg-white p-8 rounded-3xl shadow-2xl border border-orange-100">
                <span className="text-8xl">🔧</span>
              </div>
            </div>
          </div>
          
          <h2 className="text-5xl font-bold text-gray-800 mb-4">
            Sistemimiz Bakımda
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
            {maintenanceData.message}
          </p>

          {maintenanceData.eta && (
            <div className="inline-flex items-center space-x-2 bg-orange-50 px-6 py-3 rounded-full border border-orange-200">
              <span className="text-orange-600">⏰</span>
              <span className="text-gray-700">Tahmini Açılış:</span>
              <span className="font-semibold text-orange-600">
                {new Date(maintenanceData.eta).toLocaleString('tr-TR')}
              </span>
            </div>
          )}
        </div>

        {/* Kurye Notification - Özel Mesaj */}
        <div className="mb-12">
          <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 shadow-lg">
            <div className="p-6">
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-3xl">🏍️</span>
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-blue-900 mb-2">
                    📢 Kurye Arkadaşlarımıza Duyuru
                  </h3>
                  <p className="text-blue-800 text-lg mb-4">
                    Değerli kuryelerimiz, sistemimiz şu anda bakımdadır. Lütfen aktif teslimatlarınızı tamamlayın ve güvenli bir şekilde geri dönün. 
                  </p>
                  <div className="bg-white/80 p-4 rounded-lg border border-blue-200">
                    <ul className="space-y-2 text-blue-900">
                      <li className="flex items-center space-x-2">
                        <span className="text-green-500">✅</span>
                        <span>Aktif teslimatları tamamlayın</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <span className="text-green-500">✅</span>
                        <span>Müşteri ile iletişimi sürdürün</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <span className="text-yellow-500">⚠️</span>
                        <span>Yeni sipariş alımı durduruldu</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <span className="text-orange-500">🔄</span>
                        <span>Sistem açıldığında bildirim alacaksınız</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Kuryecini Tanıtımı - Görseller */}
        <div className="mb-16">
          <h3 className="text-3xl font-bold text-center text-gray-800 mb-8">
            🚀 Kuryecini Hakkında
          </h3>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {kuryeImages.map((img, index) => (
              <div key={index} className="group relative overflow-hidden rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-105">
                <img 
                  src={img} 
                  alt={`Kurye ${index + 1}`}
                  className="w-full h-64 object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="absolute bottom-4 left-4 right-4">
                    <p className="text-white font-semibold">Hızlı ve Güvenilir Teslimat</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <Card className="p-6 text-center hover:shadow-xl transition-shadow bg-gradient-to-br from-orange-50 to-white border-orange-100">
            <div className="text-5xl mb-4">⚡</div>
            <h4 className="text-xl font-bold text-gray-800 mb-2">Hızlı Teslimat</h4>
            <p className="text-gray-600">
              Siparişleriniz en hızlı şekilde kapınıza ulaşır
            </p>
          </Card>

          <Card className="p-6 text-center hover:shadow-xl transition-shadow bg-gradient-to-br from-blue-50 to-white border-blue-100">
            <div className="text-5xl mb-4">🛡️</div>
            <h4 className="text-xl font-bold text-gray-800 mb-2">Güvenilir Hizmet</h4>
            <p className="text-gray-600">
              Profesyonel kuryelerimizle güvenle teslimat
            </p>
          </Card>

          <Card className="p-6 text-center hover:shadow-xl transition-shadow bg-gradient-to-br from-green-50 to-white border-green-100">
            <div className="text-5xl mb-4">📱</div>
            <h4 className="text-xl font-bold text-gray-800 mb-2">Kolay Sipariş</h4>
            <p className="text-gray-600">
              Tek tıkla sipariş ver, anında takip et
            </p>
          </Card>
        </div>

        {/* Contact Info */}
        <Card className="bg-gradient-to-r from-gray-50 to-gray-100 border-gray-200">
          <div className="p-8 text-center">
            <h3 className="text-2xl font-bold text-gray-800 mb-6">
              📞 İletişim Bilgileri
            </h3>
            <div className="flex flex-col md:flex-row justify-center items-center space-y-4 md:space-y-0 md:space-x-8">
              <a 
                href={`mailto:${maintenanceData.contact_email}`}
                className="flex items-center space-x-2 text-gray-700 hover:text-orange-600 transition-colors"
              >
                <span className="text-2xl">📧</span>
                <span className="font-medium">{maintenanceData.contact_email}</span>
              </a>
              <a 
                href={`tel:${maintenanceData.contact_phone}`}
                className="flex items-center space-x-2 text-gray-700 hover:text-orange-600 transition-colors"
              >
                <span className="text-2xl">📱</span>
                <span className="font-medium">{maintenanceData.contact_phone}</span>
              </a>
            </div>
            
            {/* Social Media */}
            <div className="mt-6 flex justify-center space-x-4">
              <a href="https://instagram.com/kuryecini" target="_blank" rel="noopener noreferrer" 
                 className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white hover:scale-110 transition-transform">
                <span className="text-xl">📷</span>
              </a>
              <a href="https://twitter.com/kuryecini" target="_blank" rel="noopener noreferrer"
                 className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white hover:scale-110 transition-transform">
                <span className="text-xl">🐦</span>
              </a>
              <a href="https://facebook.com/kuryecini" target="_blank" rel="noopener noreferrer"
                 className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white hover:scale-110 transition-transform">
                <span className="text-xl">👥</span>
              </a>
            </div>
          </div>
        </Card>

        {/* Footer Message */}
        <div className="text-center mt-12">
          <p className="text-gray-600 text-lg">
            Anlayışınız için teşekkür ederiz. En kısa sürede tekrar hizmetinizdeyiz! 🙏
          </p>
          <div className="mt-4">
            <div className="inline-flex items-center space-x-2 text-orange-600">
              <div className="animate-spin text-2xl">⚙️</div>
              <span className="font-medium">Bakım devam ediyor...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MaintenancePage;
