import React, { useState } from "react";

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'https://delivery-nexus-5.preview.emergentagent.com/api';

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
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>🚀 Kuryecini Registration Test</h1>
      <button onClick={() => setShowRegister(!showRegister)}>
        {showRegister ? 'Hide' : 'Show'} Registration Form
      </button>
      
      {showRegister && (
        <form onSubmit={handleRegister} style={{ marginTop: '20px' }}>
          <div>
            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required
            />
          </div>
          <div>
            <input
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required
            />
          </div>
          <div>
            <input
              type="text"
              placeholder="First Name"
              value={formData.first_name}
              onChange={(e) => setFormData({...formData, first_name: e.target.value})}
              required
            />
          </div>
          <div>
            <input
              type="text"
              placeholder="Last Name"
              value={formData.last_name}
              onChange={(e) => setFormData({...formData, last_name: e.target.value})}
              required
            />
          </div>
          <button type="submit">Register Customer</button>
        </form>
      )}
    </div>
  );
}

export default App;