import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://biz-panel.preview.emergentagent.com/api';

export const AdminMessages = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMessage, setSelectedMessage] = useState(null);

  useEffect(() => {
    fetchMessages();
  }, []);

  const fetchMessages = async () => {
    try {
      setLoading(true);
      // Mock data for now
      setMessages([
        {
          id: 1,
          from: 'müşteri@example.com',
          subject: 'Sipariş Sorunu',
          message: 'Siparişim geç geldi.',
          created_at: new Date().toISOString(),
          status: 'unread'
        }
      ]);
    } catch (error) {
      console.error('Messages fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">💬 Mesajlar</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-2">
          {messages.map((msg) => (
            <Card
              key={msg.id}
              className={`cursor-pointer hover:shadow-lg transition-shadow ${
                msg.status === 'unread' ? 'border-l-4 border-blue-500' : ''
              }`}
              onClick={() => setSelectedMessage(msg)}
            >
              <CardContent className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <p className="font-medium text-sm">{msg.from}</p>
                  {msg.status === 'unread' && (
                    <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded">Yeni</span>
                  )}
                </div>
                <p className="text-sm font-semibold text-gray-800 mb-1">{msg.subject}</p>
                <p className="text-xs text-gray-500">
                  {new Date(msg.created_at).toLocaleDateString('tr-TR')}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="lg:col-span-2">
          {selectedMessage ? (
            <Card>
              <CardHeader>
                <CardTitle>{selectedMessage.subject}</CardTitle>
                <p className="text-sm text-gray-600">Gönderen: {selectedMessage.from}</p>
              </CardHeader>
              <CardContent>
                <p className="mb-4">{selectedMessage.message}</p>
                <textarea
                  placeholder="Yanıtınız..."
                  className="w-full p-3 border rounded-lg mb-3"
                  rows="4"
                />
                <Button className="bg-blue-600">📤 Yanıtla</Button>
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-gray-50">
              <CardContent className="p-12 text-center">
                <p className="text-5xl mb-4">💬</p>
                <p className="text-gray-600">Görüntülemek için bir mesaj seçin</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminMessages;