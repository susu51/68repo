import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import KuryeciniLogo from '../components/KuryeciniLogo';
import { ModernLogin } from '../ModernLogin';

const LandingPage = () => {
  const [locationInput, setLocationInput] = useState('');
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [showKVKKModal, setShowKVKKModal] = useState(false);
  const navigate = useNavigate();

  // Force light mode for landing page
  useEffect(() => {
    document.documentElement.classList.remove('dark');
    document.documentElement.style.colorScheme = 'light';
    
    // Cleanup: restore dark mode preference when unmounting
    return () => {
      const savedTheme = localStorage.getItem('kuryecini-theme');
      if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark');
        document.documentElement.style.colorScheme = 'dark';
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#F5F7FB]">
      {/* Navbar */}
      <nav className="bg-white/90 backdrop-blur border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-[1200px] mx-auto px-4 lg:px-0">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center space-x-2">
              <KuryeciniLogo width={28} height={28} useRealLogo={true} />
              <span className="text-xl font-semibold text-[#0F172A]">Kuryecini</span>
            </div>
            
            {/* Navigation Links */}
            <div className="hidden md:flex items-center space-x-8">
              <a href="#home" className="text-slate-600 hover:text-slate-900 hover:underline transition">Home</a>
              <a href="#services" className="text-slate-600 hover:text-slate-900 hover:underline transition">Services</a>
              <a href="#about" className="text-slate-600 hover:text-slate-900 hover:underline transition">About</a>
              <a href="#app" className="text-slate-600 hover:text-slate-900 hover:underline transition">App</a>
            </div>
            
            {/* Auth Buttons */}
            <div className="flex items-center space-x-3">
              <button 
                onClick={() => setShowLoginModal(true)}
                className="text-slate-700 px-4 py-2 rounded-lg font-medium hover:bg-slate-100 transition"
              >
                Giriş Yap
              </button>
              <a 
                href="/register"
                target="_blank"
                rel="noopener noreferrer"
                className="bg-[#FF7A00] text-white px-6 py-2 rounded-lg font-medium hover:bg-[#e66d00] transition shadow-lg inline-block"
              >
                Kayıt Ol
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Login Modal */}
      {showLoginModal && (
        <ModernLogin onClose={() => setShowLoginModal(false)} />
      )}

      {/* Main Content */}
      <main className="max-w-[1200px] mx-auto px-4 lg:px-0 space-y-20 py-10">
        {/* Hero Section - Dual Blocks */}
        <section className="grid lg:grid-cols-2 gap-6">
          {/* Left Panel - Customer/Order */}
          <div 
            className="bg-gradient-to-br from-[#1E90FF] to-[#2AA4FF] text-white rounded-2xl p-8 lg:p-10 relative overflow-hidden"
            style={{boxShadow: '0 10px 30px rgba(16,24,40,.08)'}}
          >
            <div className="relative z-10">
              <h1 className="text-4xl lg:text-5xl font-bold tracking-tight mb-4 leading-tight">
                Lezzetin Kapında:<br/>
                Sadece <span className="text-yellow-300">%5 Komisyonla</span><br/>
                En Hızlı Lezzet!
              </h1>
              
              <p className="text-lg text-blue-50 mb-6 leading-relaxed">
                Yüksek komisyonların fiyata yansımasına son verin. Daha uygun fiyatlarla sipariş verin.
              </p>
              
              <button 
                onClick={() => setShowLoginModal(true)}
                className="bg-white text-[#1E90FF] font-semibold px-6 py-3 rounded-lg hover:bg-blue-50 transition inline-flex items-center"
              >
                🚀 Hemen Sipariş Ver
              </button>
            </div>
            
            {/* Badge - Home Delivery */}
            <div className="absolute bottom-4 right-4 bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full text-xs font-medium">
              Home Delivery
            </div>
            
            {/* Decorative Image - Motor Kurye */}
            <img 
              src="https://customer-assets.emergentagent.com/job_kuryecini-admin-1/artifacts/al6llh3d_1760691967744.jpg" 
              alt="Kuryecini Motor Kurye" 
              className="absolute bottom-0 right-0 w-64 h-64 object-cover opacity-30 rounded-tl-3xl"
            />
          </div>

          {/* Right Panel - Courier */}
          <div 
            className="bg-[#FF7A00] text-white rounded-2xl p-8 lg:p-10 relative overflow-hidden"
            style={{boxShadow: '0 10px 30px rgba(16,24,40,.08)'}}
          >
            <div className="relative z-10">
              <h1 className="text-4xl lg:text-5xl font-bold tracking-tight mb-4 leading-tight">
                Taşıtın Ne Olursa Olsun,<br/>
                <span className="bg-white text-[#FF7A00] px-3 py-1 rounded-lg inline-block">Özgürce</span> Kazan!
              </h1>
              
              <p className="text-lg text-orange-50 mb-6 leading-relaxed">
                Ekipman, yakıt veya fatura masrafı yok. Bisikletten arabaya, kendi saatlerinde çalış.
              </p>
              
              <button 
                onClick={() => setShowLoginModal(true)}
                className="bg-white text-[#FF7A00] font-semibold px-6 py-3 rounded-lg hover:bg-orange-50 transition inline-flex items-center"
              >
                🚴 Kurye Olarak Başla
              </button>
            </div>
            
            {/* Decorative Image - Bisiklet Kurye */}
            <img 
              src="https://customer-assets.emergentagent.com/job_kuryecini-admin-1/artifacts/2nu7nag2_1760692093757.jpg" 
              alt="Kuryecini Bisiklet Kurye" 
              className="absolute bottom-0 right-0 w-64 h-64 object-cover opacity-30 rounded-tl-3xl"
            />
          </div>
        </section>

        {/* Stats Row */}
        <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-2xl p-6 text-center" style={{boxShadow: '0 10px 30px rgba(16,24,40,.08)'}}>
            <div className="text-3xl lg:text-4xl font-bold text-[#0F172A] mb-2">50.000+</div>
            <div className="text-sm text-slate-500">Mutlu Müşteri</div>
          </div>
          
          <div className="bg-white rounded-2xl p-6 text-center" style={{boxShadow: '0 10px 30px rgba(16,24,40,.08)'}}>
            <div className="text-3xl lg:text-4xl font-bold text-[#0F172A] mb-2">1.000+</div>
            <div className="text-sm text-slate-500">Restoran Ortağı</div>
          </div>
          
          <div className="bg-white rounded-2xl p-6 text-center" style={{boxShadow: '0 10px 30px rgba(16,24,40,.08)'}}>
            <div className="text-3xl lg:text-4xl font-bold text-[#0F172A] mb-2">500+</div>
            <div className="text-sm text-slate-500">Kurye Ekibi</div>
          </div>
          
          <div className="bg-white rounded-2xl p-6 text-center" style={{boxShadow: '0 10px 30px rgba(16,24,40,.08)'}}>
            <div className="text-3xl lg:text-4xl font-bold text-[#0F172A] mb-2">15 dk</div>
            <div className="text-sm text-slate-500">Ortalama Teslimat</div>
          </div>
        </section>

        {/* Vehicles Grid - MOVED UP */}
        <section>
          <h2 className="text-2xl lg:text-3xl font-semibold text-[#0F172A] text-center mb-3">
            Bisiklet, Scooter veya Araba: <span className="text-[#FF7A00]">Seçim Senin!</span>
          </h2>
          <p className="text-center text-slate-600 mb-12 max-w-2xl mx-auto">
            Hangi taşıtı kullanacağınıza siz karar verin. Sıfır maliyet, maksimum özgürlük.
          </p>
          
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Bicycle */}
            <div 
              className="bg-white rounded-2xl overflow-hidden hover:-translate-y-1 hover:shadow-lg transition-all duration-300"
              style={{boxShadow: '0 10px 30px rgba(16,24,40,.08)'}}
            >
              <img 
                src="https://customer-assets.emergentagent.com/job_kuryecini-admin-1/artifacts/2nu7nag2_1760692093757.jpg" 
                alt="Bisiklet Kurye - Kuryecini" 
                className="w-full h-48 object-cover"
              />
              <div className="p-6">
                <h3 className="font-semibold text-lg text-[#0F172A] mb-2">Bisiklet</h3>
                <p className="text-sm text-slate-600">
                  Çevreci, ekonomik ve trafikte özgür. Şehir içi teslimatlar için ideal.
                </p>
              </div>
            </div>
            
            {/* Electric Scooter - FEATURED */}
            <div 
              className="bg-white rounded-2xl overflow-hidden hover:-translate-y-1 hover:shadow-lg transition-all duration-300 relative"
              style={{boxShadow: '0 10px 30px rgba(16,24,40,.08)'}}
            >
              <div className="absolute top-3 left-3 bg-[#FF7A00] text-white px-3 py-1 rounded-md text-xs font-bold z-10">
                EN POPÜLER
              </div>
              <img 
                src="https://customer-assets.emergentagent.com/job_kuryecini-admin-1/artifacts/e4pkye7g_1760692232542.jpg" 
                alt="Motor Kurye - Kuryecini" 
                className="w-full h-48 object-cover"
              />
              <div className="p-6">
                <h3 className="font-semibold text-lg text-[#0F172A] mb-2">Motosiklet</h3>
                <p className="text-sm text-slate-600">
                  Hız ve konfor bir arada. Uzun mesafeler için mükemmel seçim.
                </p>
              </div>
            </div>
            
            {/* Car */}
            <div 
              className="bg-white rounded-2xl overflow-hidden hover:-translate-y-1 hover:shadow-lg transition-all duration-300"
              style={{boxShadow: '0 10px 30px rgba(16,24,40,.08)'}}
            >
              <img 
                src="https://customer-assets.emergentagent.com/job_kuryecini-admin-1/artifacts/al6llh3d_1760691967744.jpg" 
                alt="Van Kurye - Kuryecini" 
                className="w-full h-48 object-cover"
              />
              <div className="p-6">
                <h3 className="font-semibold text-lg text-[#0F172A] mb-2">Araç / Van</h3>
                <p className="text-sm text-slate-600">
                  Büyük siparişler, her hava şartında. Tam kontrol sizde.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Why Us - Features Grid - MOVED DOWN */}
        <section>
          <h2 className="text-2xl lg:text-3xl font-semibold text-[#0F172A] text-center mb-12">
            Neden Kuryecini?
          </h2>
          
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Hızlı Teslimat */}
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="font-semibold text-lg text-[#0F172A] mb-2">Hızlı Teslimat</h3>
              <p className="text-sm text-slate-600">15 dakikada kapınızda</p>
            </div>
            
            {/* Güvenilir */}
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 className="font-semibold text-lg text-[#0F172A] mb-2">Güvenilir</h3>
              <p className="text-sm text-slate-600">7/24 güvenli teslimat</p>
            </div>
            
            {/* Uygun Fiyat */}
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-orange-500 to-orange-600 rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-semibold text-lg text-[#0F172A] mb-2">Uygun Fiyat</h3>
              <p className="text-sm text-slate-600"><strong>Sadece %5 komisyon</strong></p>
            </div>
            
            {/* Esnek Çalışma */}
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-semibold text-lg text-[#0F172A] mb-2">Esnek Çalışma</h3>
              <p className="text-sm text-slate-600">İstediğin zaman çalış</p>
            </div>
          </div>
        </section>

        {/* Testimonials */}
        <section>
          <h2 className="text-2xl lg:text-3xl font-semibold text-[#0F172A] text-center mb-12">
            Peki Ne Diyorlar?
          </h2>
          
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Customer Testimonial */}
            <div 
              className="bg-white rounded-2xl p-6"
              style={{boxShadow: '0 10px 30px rgba(16,24,40,.08)'}}
            >
              <div className="flex items-center mb-4">
                <img 
                  src="https://i.pravatar.cc/150?img=1" 
                  alt="Müşteri" 
                  className="w-12 h-12 rounded-full mr-3"
                />
                <div>
                  <h4 className="font-semibold text-[#0F172A]">Ayşe K.</h4>
                  <p className="text-xs text-slate-500">Müşteri</p>
                </div>
              </div>
              <p className="text-sm text-slate-600">
                "15 dakikada sipariş geldi, çok memnun kaldım. Fiyatlar da gerçekten uygun!"
              </p>
            </div>
            
            {/* Restaurant Owner Testimonial */}
            <div 
              className="bg-white rounded-2xl p-6"
              style={{boxShadow: '0 10px 30px rgba(16,24,40,.08)'}}
            >
              <div className="flex items-center mb-4">
                <img 
                  src="https://i.pravatar.cc/150?img=12" 
                  alt="İşletme" 
                  className="w-12 h-12 rounded-full mr-3"
                />
                <div>
                  <h4 className="font-semibold text-[#0F172A]">Mehmet B.</h4>
                  <p className="text-xs text-slate-500">Restoran Sahibi</p>
                </div>
              </div>
              <p className="text-sm text-slate-600">
                "Düşük komisyon sayesinde müşterilerime daha iyi fiyat sunabiliyorum."
              </p>
            </div>
            
            {/* Courier Testimonial */}
            <div 
              className="bg-white rounded-2xl p-6"
              style={{boxShadow: '0 10px 30px rgba(16,24,40,.08)'}}
            >
              <div className="flex items-center mb-4">
                <img 
                  src="https://i.pravatar.cc/150?img=33" 
                  alt="Kurye" 
                  className="w-12 h-12 rounded-full mr-3"
                />
                <div>
                  <h4 className="font-semibold text-[#0F172A]">Can Y.</h4>
                  <p className="text-xs text-slate-500">Kurye</p>
                </div>
              </div>
              <p className="text-sm text-slate-600">
                "Kendi saatlerimde çalışıp iyi para kazanıyorum. Hiç ekipman masrafı yok!"
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Terms Modal */}
      {showTermsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
              <h2 className="text-2xl font-bold text-[#0F172A]">Kullanım Şartları</h2>
              <button onClick={() => setShowTermsModal(false)} className="text-gray-500 hover:text-gray-700 text-2xl">×</button>
            </div>
            <div className="px-6 py-6 space-y-6 text-gray-700">
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">1. Amaç ve Kapsam</h3>
                <p>Bu metin, Kuryecini uygulamasını kullanan müşteri, kurye ve işletmelerin hak ve yükümlülüklerini düzenler.</p>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">2. Hizmetin Tanımı</h3>
                <p>Kuryecini, kullanıcıların yemek siparişi vermesine, işletmelerin menü yayınlamasına ve kuryelerin teslimat yapmasına imkân tanıyan çevrimiçi bir platformdur.</p>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">3. Kullanıcı Yükümlülükleri</h3>
                <ul className="list-disc pl-5 space-y-2">
                  <li>Kayıt sırasında doğru ve güncel bilgi verilmesi.</li>
                  <li>Hesap bilgilerinin gizliliğinin korunması.</li>
                  <li>Platformun yasa dışı amaçlarla kullanılmaması.</li>
                </ul>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">4. Sorumluluk Reddi</h3>
                <ul className="list-disc pl-5 space-y-2">
                  <li>Teslimat süreleri, restoran yoğunluğu ve trafik koşullarına bağlı olarak değişebilir.</li>
                  <li>Kuryecini, restoranlar tarafından sunulan ürünlerin kalitesi ve içeriğinden sorumlu değildir.</li>
                </ul>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">5. Ücretlendirme ve Ödeme</h3>
                <ul className="list-disc pl-5 space-y-2">
                  <li>Ürün fiyatları, restoranlar tarafından belirlenir.</li>
                  <li>Teslimat ücreti ve komisyon oranları Kuryecini tarafından belirlenip güncellenebilir.</li>
                </ul>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">6. Hesabın Askıya Alınması</h3>
                <p>Kurallara aykırı davranışlar tespit edilirse, hesap geçici veya kalıcı olarak askıya alınabilir.</p>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">7. Uygulanacak Hukuk ve Yetki</h3>
                <p>Bu şartlar Türkiye Cumhuriyeti kanunlarına tabidir. Uyuşmazlıklarda İstanbul Mahkemeleri ve İcra Daireleri yetkilidir.</p>
              </section>
            </div>
          </div>
        </div>
      )}

      {/* Privacy Modal */}
      {showPrivacyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
              <h2 className="text-2xl font-bold text-[#0F172A]">🔒 Gizlilik Politikası</h2>
              <button onClick={() => setShowPrivacyModal(false)} className="text-gray-500 hover:text-gray-700 text-2xl">×</button>
            </div>
            <div className="px-6 py-6 space-y-6 text-gray-700">
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">1. Toplanan Veriler</h3>
                <ul className="list-disc pl-5 space-y-2">
                  <li>Kimlik bilgileri (ad, soyad, telefon, e-posta)</li>
                  <li>Konum ve adres bilgileri</li>
                  <li>Sipariş geçmişi ve ödeme bilgileri</li>
                  <li>Cihaz bilgileri (IP, tarayıcı, işletim sistemi)</li>
                </ul>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">2. Veri Kullanım Amaçları</h3>
                <ul className="list-disc pl-5 space-y-2">
                  <li>Siparişlerin işlenmesi ve teslim edilmesi</li>
                  <li>Kullanıcı deneyimini geliştirme (kişiselleştirme, öneriler)</li>
                  <li>Güvenlik ve dolandırıcılık önleme</li>
                  <li>Yasal yükümlülüklerin yerine getirilmesi</li>
                </ul>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">3. Veri Paylaşımı</h3>
                <ul className="list-disc pl-5 space-y-2">
                  <li>Restoran ve kuryeler, siparişin yerine getirilmesi için gerekli kullanıcı bilgilerini görür.</li>
                  <li>Yasal zorunluluklar halinde resmi makamlarla paylaşım yapılabilir.</li>
                  <li>Üçüncü taraf hizmet sağlayıcılar (ödeme, harita, bildirim servisleri) ile sınırlı paylaşım yapılabilir.</li>
                </ul>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">4. Veri Saklama Süresi</h3>
                <ul className="list-disc pl-5 space-y-2">
                  <li>Kullanıcı hesabı aktif olduğu sürece veriler saklanır.</li>
                  <li>Yasal yükümlülükler kapsamında belirlenen süre sonunda silinir veya anonimleştirilir.</li>
                </ul>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">5. Kullanıcı Hakları</h3>
                <ul className="list-disc pl-5 space-y-2">
                  <li>Kendi verilerini görme, güncelleme, silme talebi</li>
                  <li>Açık rıza verilen işlemlerden vazgeçme</li>
                  <li>KVKK kapsamındaki tüm başvuru hakları</li>
                </ul>
              </section>
            </div>
          </div>
        </div>
      )}

      {/* KVKK Modal */}
      {showKVKKModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
              <h2 className="text-2xl font-bold text-[#0F172A]">🛡️ KVKK Aydınlatma Metni</h2>
              <button onClick={() => setShowKVKKModal(false)} className="text-gray-500 hover:text-gray-700 text-2xl">×</button>
            </div>
            <div className="px-6 py-6 space-y-6 text-gray-700">
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">Veri Sorumlusu</h3>
                <p className="font-medium">Kuryecini Yazılım ve Teknoloji A.Ş.</p>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">İşlenen Kişisel Veriler</h3>
                <p>Kimlik bilgileri, iletişim bilgileri, adres, konum, sipariş bilgileri, ödeme bilgileri, cihaz bilgileri.</p>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">İşleme Amaçları</h3>
                <ul className="list-disc pl-5 space-y-2">
                  <li>Siparişlerin oluşturulması ve teslim edilmesi</li>
                  <li>Kullanıcı destek hizmetleri</li>
                  <li>Sistem güvenliğinin sağlanması</li>
                  <li>Yasal yükümlülüklerin yerine getirilmesi</li>
                </ul>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">Hukuki Sebepler</h3>
                <ul className="list-disc pl-5 space-y-2">
                  <li>Sözleşmenin ifası (KVKK m.5/2-c)</li>
                  <li>Hukuki yükümlülük (KVKK m.5/2-ç)</li>
                  <li>Açık rıza (KVKK m.5/1)</li>
                </ul>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">Veri Aktarımı</h3>
                <ul className="list-disc pl-5 space-y-2">
                  <li>Restoranlar ve kuryeler</li>
                  <li>Ödeme kuruluşları</li>
                  <li>Yasal merciler</li>
                </ul>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">Haklarınız</h3>
                <p>KVKK m.11 kapsamında; kişisel verilerinize erişme, düzeltme, silme, işlenmesini kısıtlama, itiraz etme ve veri taşınabilirliği hakkınız vardır.</p>
              </section>
              
              <section>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-3">Başvuru Yolu</h3>
                <p>Bu haklarınızı kullanmak için <a href="mailto:destek@kuryecini.com" className="text-blue-600 hover:underline">destek@kuryecini.com</a> adresine yazılı başvuruda bulunabilirsiniz.</p>
              </section>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-[#0F172A] text-slate-200 py-12 mt-20">
        <div className="max-w-[1200px] mx-auto px-4 lg:px-0">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            {/* Kuryecini Info */}
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center mb-4">
                <KuryeciniLogo width={32} height={32} useRealLogo={true} />
                <span className="ml-2 text-xl font-bold text-white">Kuryecini</span>
              </div>
              <p className="text-sm text-slate-400">
                Türkiye'nin en hızlı ve en uygun teslimat platformu.
              </p>
            </div>
            
            {/* Quick Links */}
            <div>
              <h4 className="font-semibold text-white mb-4">Hızlı Bağlantılar</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="text-slate-300 hover:text-white transition">Kurye Ol</a></li>
                <li><a href="#" className="text-slate-300 hover:text-white transition">Restoran Ortağı</a></li>
                <li><a href="#" className="text-slate-300 hover:text-white transition">Müşteri Desteği</a></li>
              </ul>
            </div>
            
            {/* Legal */}
            <div>
              <h4 className="font-semibold text-white mb-4">Yasal</h4>
              <ul className="space-y-2 text-sm">
                <li><button onClick={() => setShowTermsModal(true)} className="text-slate-300 hover:text-white transition">Kullanım Şartları</button></li>
                <li><button onClick={() => setShowPrivacyModal(true)} className="text-slate-300 hover:text-white transition">Gizlilik Politikası</button></li>
                <li><button onClick={() => setShowKVKKModal(true)} className="text-slate-300 hover:text-white transition">KVKK</button></li>
              </ul>
            </div>
            
            {/* Social & Payment */}
            <div>
              <h4 className="font-semibold text-white mb-4">Sosyal Medya</h4>
              <div className="flex space-x-3 mb-6">
                <a href="#" className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center hover:bg-slate-600 transition">
                  <span className="text-xs">f</span>
                </a>
                <a href="#" className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center hover:bg-slate-600 transition">
                  <span className="text-xs">in</span>
                </a>
                <a href="#" className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center hover:bg-slate-600 transition">
                  <span className="text-xs">tw</span>
                </a>
              </div>
              
              <h4 className="font-semibold text-white mb-3 text-sm">Güvenli Ödeme</h4>
              <div className="flex flex-wrap gap-2">
                <div className="bg-white px-2 py-1 rounded text-xs font-bold text-slate-900">VISA</div>
                <div className="bg-white px-2 py-1 rounded text-xs font-bold text-slate-900">MC</div>
                <div className="bg-white px-2 py-1 rounded text-xs font-bold text-blue-600">PayPal</div>
              </div>
              <div className="mt-2 flex items-center text-xs text-slate-400">
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
                256-bit SSL koruması
              </div>
            </div>
          </div>
          
          <div className="border-t border-slate-700 pt-6 text-center text-sm text-slate-400">
            <p>© 2025 Kuryecini. Tüm hakları saklıdır. Türkiye'nin en hızlı teslimat platformu.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
