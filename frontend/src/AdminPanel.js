import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Textarea } from './components/ui/textarea';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminPanel = () => {
  const [pendingCouriers, setPendingCouriers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);

  useEffect(() => {
    fetchPendingCouriers();
  }, []);

  const fetchPendingCouriers = async () => {
    try {
      const response = await axios.get(`${API}/admin/couriers/pending`);
      setPendingCouriers(response.data);
    } catch (error) {
      console.error('Error fetching pending couriers:', error);
      toast.error('Kurye listesi yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (courierId, notes = '') => {
    setProcessingId(courierId);
    try {
      await axios.post(`${API}/admin/courier/${courierId}/approve`, { notes });
      toast.success('Kurye onaylandı!');
      fetchPendingCouriers();
    } catch (error) {
      toast.error('Onaylama işlemi başarısız');
    }
    setProcessingId(null);
  };

  const handleReject = async (courierId, notes) => {
    if (!notes.trim()) {
      toast.error('Ret sebebini belirtiniz');
      return;
    }

    setProcessingId(courierId);
    try {
      await axios.post(`${API}/admin/courier/${courierId}/reject`, { notes });
      toast.success('Kurye reddedildi');
      fetchPendingCouriers();
    } catch (error) {
      toast.error('Reddetme işlemi başarısız');
    }
    setProcessingId(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Kuryeler yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4" data-testid="admin-panel">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Panel</h1>
          <p className="text-gray-600">KYC Onay Bekleyen Kuryeler</p>
        </div>

        {pendingCouriers.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <p className="text-gray-500 text-lg mb-4">Onay bekleyen kurye bulunmuyor</p>
              <p className="text-sm text-gray-400">Yeni kurye kayıtları burada görünecek</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {pendingCouriers.map((courier) => (
              <CourierCard
                key={courier.id}
                courier={courier}
                onApprove={handleApprove}
                onReject={handleReject}
                isProcessing={processingId === courier.id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const CourierCard = ({ courier, onApprove, onReject, isProcessing }) => {
  const [notes, setNotes] = useState('');
  const [showRejectForm, setShowRejectForm] = useState(false);

  return (
    <Card className="shadow-lg" data-testid={`courier-card-${courier.id}`}>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-xl">{courier.name}</CardTitle>
            <CardDescription>{courier.phone}</CardDescription>
          </div>
          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
            Onay Bekliyor
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-semibold mb-2">Kurye Bilgileri</h4>
            <div className="space-y-1 text-sm text-gray-600">
              <p><strong>Araç Türü:</strong> {getVehicleTypeName(courier.vehicle_type)}</p>
              <p><strong>Ehliyet Sınıfı:</strong> {courier.license_class}</p>
              <p><strong>Kayıt Tarihi:</strong> {new Date(courier.created_at).toLocaleDateString('tr-TR')}</p>
            </div>
          </div>
          
          <div>
            <h4 className="font-semibold mb-2">Belgeler</h4>
            <div className="space-y-2">
              {courier.license_photo_url && (
                <Button variant="outline" size="sm" className="w-full">
                  📄 Ehliyet Fotoğrafı Görüntüle
                </Button>
              )}
              {courier.vehicle_document_url && (
                <Button variant="outline" size="sm" className="w-full">
                  📋 Araç Belgesi Görüntüle
                </Button>
              )}
              {courier.profile_photo_url && (
                <Button variant="outline" size="sm" className="w-full">
                  👤 Profil Fotoğrafı Görüntüle
                </Button>
              )}
            </div>
          </div>
        </div>

        {!showRejectForm ? (
          <div className="flex gap-3 pt-4 border-t">
            <Button
              onClick={() => onApprove(courier.id)}
              disabled={isProcessing}
              className="flex-1 bg-green-600 hover:bg-green-700"
              data-testid={`approve-courier-${courier.id}`}
            >
              {isProcessing ? 'İşleniyor...' : '✅ Onayla'}
            </Button>
            <Button
              onClick={() => setShowRejectForm(true)}
              disabled={isProcessing}
              variant="destructive"
              className="flex-1"
              data-testid={`reject-courier-${courier.id}`}
            >
              ❌ Reddet
            </Button>
          </div>
        ) : (
          <div className="pt-4 border-t space-y-3">
            <div>
              <label className="block text-sm font-medium mb-2">
                Ret Sebebi <span className="text-red-500">*</span>
              </label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Neden reddedildiğini açıklayın..."
                rows={3}
                data-testid={`reject-notes-${courier.id}`}
              />
            </div>
            <div className="flex gap-3">
              <Button
                onClick={() => onReject(courier.id, notes)}
                disabled={isProcessing || !notes.trim()}
                variant="destructive"
                className="flex-1"
                data-testid={`confirm-reject-${courier.id}`}
              >
                {isProcessing ? 'İşleniyor...' : '❌ Reddet'}
              </Button>
              <Button
                onClick={() => {
                  setShowRejectForm(false);
                  setNotes('');
                }}
                variant="outline"
                className="flex-1"
              >
                İptal
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const getVehicleTypeName = (type) => {
  const types = {
    araba: 'Araba',
    motor: 'Motor',
    elektrikli_motor: 'Elektrikli Motor',
    bisiklet: 'Bisiklet'
  };
  return types[type] || type;
};

export default AdminPanel;