import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { getCityNames, getDistrictsByCity } from '../data/turkeyLocations';

const ModernRegister = ({ onSuccess, onBack }) => {
  const [step, setStep] = useState(1); // 1: Role, 2: Personal Info, 3: Location, 4: Documents
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    // Personal
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    phone: '',
    
    // Location
    city: '',
    district: '',
    neighborhood: '',
    
    // Courier specific
    vehicle_type: '',
    license_photo: null,
    id_photo: null,
    vehicle_photo: null,
    
    // Business specific
    business_name: '',
    business_tax_id: '',
    business_photo: null
  });

  const cities = getCityNames();
  const districts = formData.city ? getDistrictsByCity(formData.city) : [];

  const handleFileChange = (field, file) => {
    if (file && file.size > 5 * 1024 * 1024) {
      toast.error('Dosya boyutu 5MB\'dan küçük olmalıdır');
      return;
    }
    setFormData({ ...formData, [field]: file });
  };

  const handleSubmit = async () => {
    setLoading(true);
    
    try {
      const formDataToSend = new FormData();
      
      // Add text fields
      const textFields = ['first_name', 'last_name', 'email', 'password', 'phone', 'city', 'district', 'neighborhood', 'vehicle_type', 'business_name', 'business_tax_id'];
      textFields.forEach(key => {
        if (formData[key] && formData[key] !== '') {
          formDataToSend.append(key, formData[key]);
        }
      });
      
      // Add file fields - check if they're File objects
      const fileFields = ['license_photo', 'id_photo', 'vehicle_photo', 'business_photo'];
      fileFields.forEach(key => {
        if (formData[key] && formData[key] instanceof File) {
          formDataToSend.append(key, formData[key]);
          console.log(`📎 Uploading ${key}:`, formData[key].name);
        }
      });
      
      formDataToSend.append('role', role);
      
      console.log('📤 Submitting registration for role:', role);

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || ''}/api/auth/register`, {
        method: 'POST',
        body: formDataToSend,
        credentials: 'include'
      });

      const data = await response.json();

      if (data.success) {
        const roleNames = { customer: 'Müşteri', courier: 'Kurye', business: 'İşletme' };
        const needsApproval = role === 'courier' || role === 'business';
        
        toast.success(
          needsApproval 
            ? `✅ ${roleNames[role]} kaydınız alındı! Admin onayından sonra sistemi kullanabileceksiniz.`
            : `✅ ${roleNames[role]} kaydınız tamamlandı! Hoş geldiniz!`
        );
        
        if (onSuccess) onSuccess(data);
      } else {
        throw new Error(data.detail || 'Kayıt başarısız');
      }
    } catch (error) {
      console.error('Register error:', error);
      toast.error(error.message || 'Kayıt sırasında bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  // Step 1: Role Selection
  const RoleSelection = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Nasıl Kayıt Olmak İstersiniz?</h2>
        <p className="text-gray-600">Rolünüzü seçerek başlayın</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { id: 'customer', icon: '🛒', title: 'Müşteri', desc: 'Sipariş vermek için' },
          { id: 'courier', icon: '🏍️', title: 'Kurye', desc: 'Teslimat yapmak için' },
          { id: 'business', icon: '🏪', title: 'İşletme', desc: 'Restoran/işletme olarak' }
        ].map(item => (
          <button
            key={item.id}
            onClick={() => {
              setRole(item.id);
              setStep(2);
            }}
            className="group p-8 border-2 border-gray-200 rounded-2xl hover:border-orange-500 hover:shadow-xl transition-all duration-300 text-center bg-white"
          >
            <div className="text-6xl mb-4 transform group-hover:scale-110 transition-transform">{item.icon}</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2 group-hover:text-orange-600">{item.title}</h3>
            <p className="text-gray-600">{item.desc}</p>
          </button>
        ))}
      </div>
    </div>
  );

  // Step 2: Personal Info
  const PersonalInfo = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Kişisel Bilgiler</h2>
          <p className="text-gray-600">Adınız ve iletişim bilgilerinizi girin</p>
        </div>
        <div className="text-4xl">
          {role === 'customer' && '🛒'}
          {role === 'courier' && '🏍️'}
          {role === 'business' && '🏪'}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {role === 'business' && (
          <>
            <input
              type="text"
              placeholder="İşletme/Restoran Adı *"
              value={formData.business_name}
              onChange={(e) => setFormData({...formData, business_name: e.target.value})}
              className="col-span-2 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              required
            />
            <input
              type="text"
              placeholder="Vergi Numarası *"
              value={formData.business_tax_id}
              onChange={(e) => setFormData({...formData, business_tax_id: e.target.value})}
              className="col-span-2 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              required
            />
            <div className="col-span-2 text-sm text-gray-600 font-medium">Yetkili Kişi Bilgileri:</div>
          </>
        )}
        
        <input
          type="text"
          placeholder="Adınız *"
          value={formData.first_name}
          onChange={(e) => setFormData({...formData, first_name: e.target.value})}
          className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
        />
        <input
          type="text"
          placeholder="Soyadınız *"
          value={formData.last_name}
          onChange={(e) => setFormData({...formData, last_name: e.target.value})}
          className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
        />
        <input
          type="tel"
          placeholder="Telefon (05XX XXX XX XX) *"
          value={formData.phone}
          onChange={(e) => setFormData({...formData, phone: e.target.value})}
          className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
        />
        <input
          type="email"
          placeholder="E-posta *"
          value={formData.email}
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
        />
        <input
          type="password"
          placeholder="Şifre (min. 6 karakter) *"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          className="col-span-2 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
        />
      </div>

      <div className="flex justify-between pt-4">
        <button
          onClick={() => setStep(1)}
          className="px-6 py-3 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50"
        >
          ← Geri
        </button>
        <button
          onClick={() => setStep(3)}
          className="px-8 py-3 bg-orange-600 text-white rounded-xl hover:bg-orange-700"
        >
          İleri →
        </button>
      </div>
    </div>
  );

  // Step 3: Location
  const LocationInfo = () => (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Konum Bilgileri</h2>
        <p className="text-gray-600">Şehir, ilçe ve mahalle bilgilerinizi girin</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <select
          value={formData.city}
          onChange={(e) => setFormData({...formData, city: e.target.value, district: '', neighborhood: ''})}
          className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
        >
          <option value="">İl Seçin *</option>
          {cities.map(city => (
            <option key={city} value={city}>{city}</option>
          ))}
        </select>

        <select
          value={formData.district}
          onChange={(e) => setFormData({...formData, district: e.target.value})}
          className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
          disabled={!formData.city}
        >
          <option value="">İlçe Seçin *</option>
          {districts.map(district => (
            <option key={district} value={district}>{district}</option>
          ))}
        </select>

        <input
          type="text"
          placeholder="Mahalle/Köy *"
          value={formData.neighborhood}
          onChange={(e) => setFormData({...formData, neighborhood: e.target.value})}
          className="col-span-2 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
        />

        {role === 'courier' && (
          <select
            value={formData.vehicle_type}
            onChange={(e) => setFormData({...formData, vehicle_type: e.target.value})}
            className="col-span-2 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            required
          >
            <option value="">Araç Tipi Seçin *</option>
            <option value="bicycle">🚲 Bisiklet</option>
            <option value="motorbike">🏍️ Motosiklet</option>
            <option value="car">🚗 Araba</option>
            <option value="van">🚚 Minivan</option>
          </select>
        )}
      </div>

      <div className="flex justify-between pt-4">
        <button
          onClick={() => setStep(2)}
          className="px-6 py-3 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50"
        >
          ← Geri
        </button>
        <button
          onClick={() => {
            if (role === 'customer') {
              handleSubmit();
            } else {
              setStep(4);
            }
          }}
          className="px-8 py-3 bg-orange-600 text-white rounded-xl hover:bg-orange-700"
          disabled={loading}
        >
          {loading ? 'Kaydediliyor...' : role === 'customer' ? 'Kaydı Tamamla ✓' : 'İleri →'}
        </button>
      </div>
    </div>
  );

  // Step 4: Documents (Courier & Business only)
  const DocumentsUpload = () => (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Belgeler</h2>
        <p className="text-gray-600">
          {role === 'courier' ? 'Ehliyet, kimlik ve araç ruhsatınızı yükleyin' : 'İşletme fotoğrafınızı yükleyin'}
        </p>
      </div>

      {role === 'courier' && (
        <div className="space-y-4">
          {[
            { field: 'license_photo', label: '📄 Ehliyet Fotoğrafı', icon: '🪪' },
            { field: 'id_photo', label: '🪪 Kimlik Fotoğrafı', icon: '👤' },
            { field: 'vehicle_photo', label: '🚗 Araç Ruhsat Fotoğrafı', icon: '📋' }
          ].map(item => (
            <div key={item.field} className="border-2 border-dashed border-gray-300 rounded-xl p-6 hover:border-orange-500 transition-colors">
              <label className="flex items-center justify-between cursor-pointer">
                <div className="flex items-center space-x-3">
                  <span className="text-3xl">{item.icon}</span>
                  <div>
                    <div className="font-medium text-gray-900">{item.label} *</div>
                    {formData[item.field] && (
                      <div className="text-sm text-green-600">✓ {formData[item.field].name}</div>
                    )}
                  </div>
                </div>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleFileChange(item.field, e.target.files[0])}
                  className="hidden"
                  required
                />
                <span className="px-4 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200">
                  {formData[item.field] ? 'Değiştir' : 'Seç'}
                </span>
              </label>
            </div>
          ))}
        </div>
      )}

      {role === 'business' && (
        <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 hover:border-orange-500 transition-colors">
          <label className="flex flex-col items-center cursor-pointer">
            <span className="text-6xl mb-4">🏪</span>
            <div className="text-center">
              <div className="font-medium text-gray-900 mb-2">İşletme Fotoğrafı *</div>
              {formData.business_photo && (
                <div className="text-sm text-green-600 mb-2">✓ {formData.business_photo.name}</div>
              )}
              <span className="px-6 py-3 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 inline-block">
                {formData.business_photo ? 'Değiştir' : 'Fotoğraf Seç'}
              </span>
            </div>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => handleFileChange('business_photo', e.target.files[0])}
              className="hidden"
              required
            />
          </label>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <div className="flex items-start space-x-2">
          <span className="text-xl">ℹ️</span>
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Önemli Bilgi:</p>
            <p>Yüklediğiniz belgeler admin tarafından incelenecektir. Onay sonrası hesabınız aktif olacaktır.</p>
          </div>
        </div>
      </div>

      <div className="flex justify-between pt-4">
        <button
          onClick={() => setStep(3)}
          className="px-6 py-3 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50"
          disabled={loading}
        >
          ← Geri
        </button>
        <button
          onClick={handleSubmit}
          className="px-8 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 disabled:opacity-50"
          disabled={loading || (role === 'courier' && (!formData.license_photo || !formData.id_photo || !formData.vehicle_photo)) || (role === 'business' && !formData.business_photo)}
        >
          {loading ? 'Kaydediliyor...' : 'Kaydı Tamamla ✓'}
        </button>
      </div>
    </div>
  );

  // Progress Bar
  const ProgressBar = () => {
    const maxStep = role === 'customer' ? 3 : 4;
    const progress = (step / maxStep) * 100;
    
    return (
      <div className="mb-8">
        <div className="flex justify-between mb-2">
          {['Rol', 'Bilgiler', 'Konum', role !== 'customer' && 'Belgeler'].filter(Boolean).map((label, i) => (
            <div key={i} className={`text-sm font-medium ${step > i + 1 ? 'text-green-600' : step === i + 1 ? 'text-orange-600' : 'text-gray-400'}`}>
              {label}
            </div>
          ))}
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-orange-500 to-orange-600 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-orange-50 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl bg-white rounded-3xl shadow-2xl p-8 md:p-12">
        {step > 1 && <ProgressBar />}
        
        {step === 1 && <RoleSelection />}
        {step === 2 && <PersonalInfo />}
        {step === 3 && <LocationInfo />}
        {step === 4 && <DocumentsUpload />}

        {step === 1 && onBack && (
          <div className="text-center mt-6">
            <button
              onClick={onBack}
              className="text-gray-600 hover:text-gray-800 underline"
            >
              ← Giriş sayfasına dön
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ModernRegister;
