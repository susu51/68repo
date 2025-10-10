import React, { useState } from 'react';
import toast from 'react-hot-toast';

const SimpleLogin = ({ onClose, onLogin }) => {
  const [email, setEmail] = useState('testcustomer@example.com');
  const [password, setPassword] = useState('test123');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log('🚀 SIMPLE LOGIN: Attempting login with:', { email });
      
      const response = await fetch('http://localhost:8001/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ email, password })
      });
      
      console.log('🚀 Response status:', response.status);
      
      if (response.ok) {
        const result = await response.json();
        console.log('🚀 Login success:', result);
        
        // Store token
        if (result.access_token) {
          localStorage.setItem('access_token', result.access_token);
        }
        
        // Close modal and notify success
        onClose && onClose();
        onLogin && onLogin({ success: true, ...result });
        toast.success('✅ Giriş başarılı!');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Giriş başarısız');
      }
    } catch (error) {
      console.error('🚀 Login error:', error);
      toast.error(`Giriş hatası: ${error.message}`);
    }
    
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-8 rounded-lg max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Simple Login Test</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email:</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Password:</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          
          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Giriş yapılıyor...' : '🚀 Basit Giriş'}
          </button>
        </form>
        
        <div className="mt-4 text-sm text-gray-600">
          <p>Test accounts:</p>
          <p>• testcustomer@example.com / test123</p>
          <p>• admin@kuryecini.com / KuryeciniAdmin2024!</p>
        </div>
      </div>
    </div>
  );
};

export default SimpleLogin;