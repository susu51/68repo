import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import api from '../api/http';

const MessageCenter = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    recipient_type: 'courier',
    recipient_id: '',
    subject: '',
    message: ''
  });

  useEffect(() => {
    fetchMessages();
  }, []);

  const fetchMessages = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/messages');
      const data = await response.json();
      setMessages(data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      
      const response = await api('/admin/messages', {
        method: 'POST',
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Mesaj gönderildi! (${result.count} alıcı)`);
        setShowForm(false);
        setFormData({
          recipient_type: 'courier',
          recipient_id: '',
          subject: '',
          message: ''
        });
        fetchMessages();
      } else {
        const error = await response.json();
        alert(error.detail || 'Hata oluştu');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Gönderme hatası');
    } finally {
      setLoading(false);
    }
  };

  const getRecipientTypeLabel = (type) => {
    const labels = {
      'courier': 'Kurye',
      'business': 'İşletme',
      'all_couriers': 'Tüm Kuryeler',
      'all_businesses': 'Tüm İşletmeler'
    };
    return labels[type] || type;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">💬 Mesaj Merkezi</h2>
        <Button onClick={() => {
          setShowForm(!showForm);
          setFormData({
            recipient_type: 'courier',
            recipient_id: '',
            subject: '',
            message: ''
          });
        }}>
          {showForm ? 'İptal' : '+ Yeni Mesaj Gönder'}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Yeni Mesaj Gönder</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label>Alıcı Türü *</Label>
                <Select
                  value={formData.recipient_type}
                  onValueChange={(value) => setFormData({...formData, recipient_type: value, recipient_id: ''})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="courier">Tek Kurye</SelectItem>
                    <SelectItem value="business">Tek İşletme</SelectItem>
                    <SelectItem value="all_couriers">Tüm Kuryeler</SelectItem>
                    <SelectItem value="all_businesses">Tüm İşletmeler</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {(formData.recipient_type === 'courier' || formData.recipient_type === 'business') && (
                <div>
                  <Label>Alıcı ID *</Label>
                  <Input
                    value={formData.recipient_id}
                    onChange={(e) => setFormData({...formData, recipient_id: e.target.value})}
                    placeholder={`${formData.recipient_type === 'courier' ? 'Kurye' : 'İşletme'} ID'sini girin`}
                    required
                  />
                </div>
              )}

              <div>
                <Label>Konu *</Label>
                <Input
                  value={formData.subject}
                  onChange={(e) => setFormData({...formData, subject: e.target.value})}
                  placeholder="Mesaj konusu"
                  required
                />
              </div>

              <div>
                <Label>Mesaj *</Label>
                <Textarea
                  value={formData.message}
                  onChange={(e) => setFormData({...formData, message: e.target.value})}
                  placeholder="Mesaj içeriği..."
                  rows={5}
                  required
                />
              </div>

              <Button type="submit" disabled={loading}>
                {loading ? 'Gönderiliyor...' : 'Gönder'}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        <h3 className="font-semibold text-lg">Gönderilen Mesajlar</h3>
        {messages.map((msg) => (
          <Card key={msg.id}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold">{msg.subject}</span>
                    <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700">
                      {getRecipientTypeLabel(msg.recipient_type)}
                    </span>
                    {msg.is_read && (
                      <span className="text-xs px-2 py-1 rounded bg-green-100 text-green-700">
                        ✓ Okundu
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{msg.message}</p>
                  <p className="text-xs text-gray-400 mt-2">
                    {new Date(msg.created_at).toLocaleString('tr-TR')}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {messages.length === 0 && !loading && (
        <div className="text-center py-12 text-gray-500">
          Henüz mesaj gönderilmemiş.
        </div>
      )}
    </div>
  );
};

export default MessageCenter;
