import React from 'react';

const PersonalInfoStep = React.memo(({ 
  role, 
  formData, 
  onInputChange, 
  onNext, 
  onBack 
}) => {
  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <div>
          <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-gray-900">Kişisel Bilgiler</h2>
          <p className="text-xs sm:text-sm md:text-base text-gray-600">Adınız ve iletişim bilgilerinizi girin</p>
        </div>
        <div className="text-2xl sm:text-3xl md:text-4xl">
          {role === 'customer' && '🛒'}
          {role === 'courier' && '🏍️'}
          {role === 'business' && '🏪'}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
        {role === 'business' && (
          <>
            <input
              type="text"
              name="business_name"
              placeholder="İşletme/Restoran Adı *"
              value={formData.business_name}
              onChange={(e) => onInputChange('business_name', e.target.value)}
              className="col-span-1 md:col-span-2 px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base border border-gray-300 rounded-lg sm:rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              required
            />
            <input
              type="text"
              name="business_tax_id"
              placeholder="Vergi Numarası *"
              value={formData.business_tax_id}
              onChange={(e) => onInputChange('business_tax_id', e.target.value)}
              className="col-span-1 md:col-span-2 px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base border border-gray-300 rounded-lg sm:rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              required
            />
            <div className="col-span-1 md:col-span-2 text-xs sm:text-sm text-gray-600 font-medium">Yetkili Kişi Bilgileri:</div>
          </>
        )}
        
        <input
          type="text"
          name="first_name"
          placeholder="Adınız *"
          value={formData.first_name}
          onChange={(e) => onInputChange('first_name', e.target.value)}
          className="px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base border border-gray-300 rounded-lg sm:rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
        />
        <input
          type="text"
          name="last_name"
          placeholder="Soyadınız *"
          value={formData.last_name}
          onChange={(e) => onInputChange('last_name', e.target.value)}
          className="px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base border border-gray-300 rounded-lg sm:rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
        />
        <input
          type="tel"
          name="phone"
          placeholder="Telefon (05XX XXX XX XX) *"
          value={formData.phone}
          onChange={(e) => onInputChange('phone', e.target.value)}
          className="px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base border border-gray-300 rounded-lg sm:rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
        />
        <input
          type="email"
          name="email"
          placeholder="E-posta *"
          value={formData.email}
          onChange={(e) => onInputChange('email', e.target.value)}
          className="px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base border border-gray-300 rounded-lg sm:rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
        />
        <input
          type="password"
          name="password"
          placeholder="Şifre (min. 6 karakter) *"
          value={formData.password}
          onChange={(e) => onInputChange('password', e.target.value)}
          className="col-span-1 md:col-span-2 px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base border border-gray-300 rounded-lg sm:rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          required
        />
      </div>

      <div className="flex flex-col sm:flex-row justify-between gap-2 sm:gap-0 pt-3 sm:pt-4">
        <button
          type="button"
          onClick={onBack}
          className="px-4 sm:px-6 py-2 sm:py-3 text-sm sm:text-base border border-gray-300 rounded-lg sm:rounded-xl text-gray-700 hover:bg-gray-50 order-2 sm:order-1"
        >
          ← Geri
        </button>
        <button
          type="button"
          onClick={onNext}
          className="px-6 sm:px-8 py-2 sm:py-3 text-sm sm:text-base bg-orange-600 text-white rounded-lg sm:rounded-xl hover:bg-orange-700 order-1 sm:order-2"
        >
          İleri →
        </button>
      </div>
    </div>
  );
});

PersonalInfoStep.displayName = 'PersonalInfoStep';

export default PersonalInfoStep;
