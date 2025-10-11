import React, { useState } from "react";

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'https://quickcourier.preview.emergentagent.com/api';

console.log('Minimal App loaded, API_BASE:', API_BASE);

function App() {
  const [showRegister, setShowRegister] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: ''
  });

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/auth/register?role=customer`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...formData,
          role: 'customer'
        })
      });
      
      const result = await response.json();
      alert('Registration successful: ' + JSON.stringify(result));
    } catch (error) {
      alert('Registration failed: ' + error.message);
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Header */}
      <header style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        padding: '1rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 20px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ 
            fontSize: '24px', 
            fontWeight: 'bold', 
            color: '#667eea',
            letterSpacing: '-0.5px'
          }}>
            🚀 Kuryecini
          </div>
        </div>
        <button 
          onClick={() => setShowRegister(!showRegister)}
          style={{
            background: showRegister ? '#dc3545' : '#667eea',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '25px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            fontSize: '14px'
          }}
        >
          {showRegister ? 'Gizle' : 'Kayıt Ol'}
        </button>
      </header>

      {/* Hero Section */}
      <main style={{ padding: '4rem 2rem', textAlign: 'center', color: 'white' }}>
        <h1 style={{ 
          fontSize: '3.5rem', 
          fontWeight: '700', 
          marginBottom: '1rem',
          textShadow: '2px 2px 4px rgba(0,0,0,0.3)'
        }}>
          Hızlı ve Güvenli Teslimat
        </h1>
        <p style={{ 
          fontSize: '1.25rem', 
          marginBottom: '2rem', 
          opacity: '0.9',
          maxWidth: '600px',
          margin: '0 auto 3rem'
        }}>
          İstanbul'un her yerine dakikalar içinde teslimat. 
          Yemek siparişinden kargo gönderime, her ihtiyacınız için buradayız.
        </p>
        
        {showRegister && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            padding: '2rem',
            borderRadius: '15px',
            maxWidth: '400px',
            margin: '0 auto',
            boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
          }}>
            <h2 style={{ color: '#333', marginBottom: '1.5rem', fontSize: '1.5rem' }}>
              Müşteri Kaydı
            </h2>
            <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <input
                type="email"
                placeholder="E-posta adresiniz"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
                style={{
                  padding: '12px 16px',
                  border: '2px solid #e1e5e9',
                  borderRadius: '8px',
                  fontSize: '16px',
                  outline: 'none',
                  transition: 'border-color 0.3s ease'
                }}
              />
              <input
                type="password"
                placeholder="Şifreniz (min. 6 karakter)"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
                minLength={6}
                style={{
                  padding: '12px 16px',
                  border: '2px solid #e1e5e9',
                  borderRadius: '8px',
                  fontSize: '16px',
                  outline: 'none'
                }}
              />
              <input
                type="text"
                placeholder="Adınız"
                value={formData.first_name}
                onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                required
                style={{
                  padding: '12px 16px',
                  border: '2px solid #e1e5e9',
                  borderRadius: '8px',
                  fontSize: '16px',
                  outline: 'none'
                }}
              />
              <input
                type="text"
                placeholder="Soyadınız"
                value={formData.last_name}
                onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                required
                style={{
                  padding: '12px 16px',
                  border: '2px solid #e1e5e9',
                  borderRadius: '8px',
                  fontSize: '16px',
                  outline: 'none'
                }}
              />
              <button type="submit" style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                border: 'none',
                padding: '14px 24px',
                borderRadius: '8px',
                fontWeight: '600',
                fontSize: '16px',
                cursor: 'pointer',
                transition: 'transform 0.2s ease'
              }}>
                Kayıt Ol
              </button>
            </form>
          </div>
        )}
        
        {!showRegister && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '2rem',
            marginTop: '3rem',
            maxWidth: '900px',
            margin: '3rem auto 0'
          }}>
            <div style={{
              background: 'rgba(255, 255, 255, 0.1)',
              padding: '2rem',
              borderRadius: '15px',
              backdropFilter: 'blur(10px)'
            }}>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>🍕 Yemek Siparişi</h3>
              <p>Favori restoranlarınızdan hızlı teslimat</p>
            </div>
            <div style={{
              background: 'rgba(255, 255, 255, 0.1)',
              padding: '2rem',
              borderRadius: '15px',
              backdropFilter: 'blur(10px)'
            }}>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>📦 Kargo Teslimat</h3>
              <p>Paketlerinizi güvenle teslim edelim</p>
            </div>
            <div style={{
              background: 'rgba(255, 255, 255, 0.1)',
              padding: '2rem',
              borderRadius: '15px',
              backdropFilter: 'blur(10px)'
            }}>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>🚴‍♂️ Hızlı Servis</h3>
              <p>Dakikalar içinde kapınızda</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;