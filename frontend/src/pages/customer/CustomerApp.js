import React from 'react';

export const CustomerApp = ({ user, onLogout }) => {
  console.log('🚀 Simple CustomerApp rendered - user:', user?.first_name);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Kuryecini Customer App
        </h1>
        <p className="text-gray-600 mb-4">
          Hoş geldin {user?.first_name || 'Müşteri'}!
        </p>
        <p className="text-sm text-green-600">
          ✅ Render error çözüldü - Basit version çalışıyor
        </p>
      </div>
    </div>
  );
};

export default CustomerApp;