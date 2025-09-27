import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Badge } from './components/ui/badge';
import { Textarea } from './components/ui/textarea';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Checkbox } from './components/ui/checkbox';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Package Details Component
const PackageDetailsForm = ({ packageDetails, setPackageDetails }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Paket Detayları</CardTitle>
        <CardDescription>Gönderilecek paket hakkında bilgi verin</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="weight">Ağırlık (kg)</Label>
            <Input
              id="weight"
              type="number"
              step="0.1"
              min="0.1"
              max="50"
              placeholder="2.5"
              value={packageDetails.weight_kg}
              onChange={(e) => setPackageDetails({
                ...packageDetails,
                weight_kg: parseFloat(e.target.value) || 0
              })}
              required
              data-testid="package-weight"
            />
          </div>
          
          <div>
            <Label htmlFor="dimensions">Boyutlar (cm)</Label>
            <Input
              id="dimensions"
              placeholder="30x20x15"
              value={packageDetails.dimensions || ''}
              onChange={(e) => setPackageDetails({
                ...packageDetails,
                dimensions: e.target.value
              })}
              data-testid="package-dimensions"
            />
          </div>
        </div>
        
        <div>
          <Label>Teslimat Önceliği</Label>
          <Select 
            value={packageDetails.priority}
            onValueChange={(value) => setPackageDetails({
              ...packageDetails,
              priority: value
            })}
          >
            <SelectTrigger data-testid="package-priority">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="normal">
                <div className="flex items-center gap-2">
                  <span>📦 Normal</span>
                  <Badge variant="secondary">Standart</Badge>
                </div>
              </SelectItem>
              <SelectItem value="express">
                <div className="flex items-center gap-2">
                  <span>⚡ Express</span>
                  <Badge className="bg-orange-100 text-orange-800">+%50 ücret</Badge>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label htmlFor="floor">Kat Numarası (Opsiyonel)</Label>
          <Input
            id="floor"
            type="number"
            min="-5"
            max="50"
            placeholder="3"
            value={packageDetails.floor_number || ''}
            onChange={(e) => setPackageDetails({
              ...packageDetails,
              floor_number: e.target.value ? parseInt(e.target.value) : null
            })}
            data-testid="package-floor"
          />
        </div>
        
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="fragile"
              checked={packageDetails.is_fragile}
              onCheckedChange={(checked) => setPackageDetails({
                ...packageDetails,
                is_fragile: checked
              })}
              data-testid="package-fragile"
            />
            <Label htmlFor="fragile" className="flex items-center gap-2">
              💔 Kırılabilir Ürün
              <Badge variant="outline">Özel dikkat</Badge>
            </Label>
          </div>
          
          <div className="flex items-center space-x-2">
            <Checkbox
              id="cold-chain"
              checked={packageDetails.requires_cold_chain}
              onCheckedChange={(checked) => setPackageDetails({
                ...packageDetails,
                requires_cold_chain: checked
              })}
              data-testid="package-cold-chain"
            />
            <Label htmlFor="cold-chain" className="flex items-center gap-2">
              ❄️ Soğuk Zincir
              <Badge variant="outline">Soğuk muhafaza</Badge>
            </Label>
          </div>
        </div>
        
        <div>
          <Label htmlFor="special-instructions">Özel Talimatlar</Label>
          <Textarea
            id="special-instructions"
            placeholder="Kurye için özel notlar (kapı kodu, teslim yeri vb.)"
            value={packageDetails.special_instructions || ''}
            onChange={(e) => setPackageDetails({
              ...packageDetails,
              special_instructions: e.target.value
            })}
            data-testid="package-instructions"
          />
        </div>
      </CardContent>
    </Card>
  );
};

// Pricing Display Component
const PricingDisplay = ({ pricing, packageDetails }) => {
  if (!pricing) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Teslimat Ücreti</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span>Baz Ücret:</span>
            <span>₺{pricing.base_price?.toFixed(2)}</span>
          </div>
          
          <div className="flex justify-between text-sm">
            <span>Mesafe Ücreti:</span>
            <span>₺{pricing.distance_cost?.toFixed(2)}</span>
          </div>
          
          {packageDetails.priority === 'express' && (
            <div className="flex justify-between text-sm text-orange-600">
              <span>Express Ekstra (%50):</span>
              <span>₺{((pricing.total_delivery_fee || 0) * 0.33).toFixed(2)}</span>
            </div>
          )}
          
          {packageDetails.weight_kg > 5 && (
            <div className="flex justify-between text-sm text-blue-600">
              <span>Ağırlık Ekstra (&gt;5kg):</span>
              <span>₺{((packageDetails.weight_kg - 5) * (pricing.base_price || 0) * 0.1).toFixed(2)}</span>
            </div>
          )}
          
          <div className="border-t pt-3 flex justify-between font-semibold">
            <span>Toplam Ücret:</span>
            <span className="text-green-600">₺{pricing.total_delivery_fee?.toFixed(2)}</span>
          </div>
          
          <div className="text-xs text-gray-500 space-y-1">
            <div>Platform komisyonu (%3): ₺{pricing.commission?.toFixed(2)}</div>
            <div>Kurye kazancı: ₺{pricing.courier_earning?.toFixed(2)}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Main Package Order Component
export const CreatePackageOrder = ({ onOrderCreated, onCancel }) => {
  const [pickupAddress, setPickupAddress] = useState('');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [packageDetails, setPackageDetails] = useState({
    weight_kg: 1,
    dimensions: '',
    is_fragile: false,
    requires_cold_chain: false,
    priority: 'normal',
    floor_number: null,
    special_instructions: ''
  });
  const [recipientInfo, setRecipientInfo] = useState({
    name: '',
    phone: ''
  });
  const [orderNotes, setOrderNotes] = useState('');
  const [pricing, setPricing] = useState(null);
  const [loading, setLoading] = useState(false);

  // Calculate pricing when addresses or package details change
  useEffect(() => {
    if (pickupAddress && deliveryAddress && packageDetails.weight_kg > 0) {
      calculatePricing();
    }
  }, [pickupAddress, deliveryAddress, packageDetails]);

  const calculatePricing = () => {
    // Mock pricing calculation (in real app, this would be an API call)
    // Since we don't have coordinates, we'll use a fixed distance for demo
    const distance = 5.0; // Fixed 5km distance for demo
    
    const basePrice = 12.0;
    const pricePerKm = 3.0;
    const distanceCost = distance * pricePerKm;
    
    let total = basePrice + distanceCost;
    
    // Priority multiplier
    if (packageDetails.priority === 'express') {
      total *= 1.5;
    }
    
    // Weight multiplier
    if (packageDetails.weight_kg > 5) {
      total += (packageDetails.weight_kg - 5) * basePrice * 0.1;
    }
    
    const commission = total * 0.03;
    const courierEarning = (total - commission) * 0.85;
    
    setPricing({
      base_price: basePrice,
      distance_cost: distanceCost,
      total_delivery_fee: total,
      commission: commission,
      courier_earning: courierEarning
    });
  };

  const calculateDistance = (lat1, lng1, lat2, lng2) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
      Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!pickupAddress || !deliveryAddress) {
      toast.error('Alış ve teslim adreslerini giriniz');
      return;
    }

    if (!recipientInfo.name || !recipientInfo.phone) {
      toast.error('Alıcı bilgilerini doldurunuz');
      return;
    }

    setLoading(true);
    try {
      const orderData = {
        pickup_address: {
          lat: 41.0082, // Demo coordinates for Istanbul
          lon: 28.9784,
          address: pickupAddress,
          city: "İstanbul"
        },
        delivery_address: {
          lat: 41.0082, // Demo coordinates for Istanbul
          lon: 28.9784,
          address: deliveryAddress,
          city: "İstanbul"
        },
        package_details: packageDetails,
        recipient_name: recipientInfo.name,
        recipient_phone: recipientInfo.phone,
        order_notes: orderNotes
      };

      const token = localStorage.getItem('delivertr_token');
      const response = await axios.post(`${API}/orders/create-package`, orderData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Paket siparişi oluşturuldu!');
      if (onOrderCreated) {
        onOrderCreated(response.data.order_id);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Sipariş oluşturulamadı');
    }
    setLoading(false);
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>Paket Gönder</CardTitle>
        <CardDescription>Paketinizi güvenle teslim edelim</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Addresses */}
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <Label className="text-base font-semibold">Alış Adresi</Label>
              <div className="mt-2">
                <Textarea
                  value={pickupAddress}
                  onChange={(e) => setPickupAddress(e.target.value)}
                  placeholder="Paket alınacak adres (tam adres bilgisi)"
                  rows="3"
                />
              </div>
            </div>
            
            <div>
              <Label className="text-base font-semibold">Teslim Adresi</Label>
              <div className="mt-2">
                <Textarea
                  value={deliveryAddress}
                  onChange={(e) => setDeliveryAddress(e.target.value)}
                  placeholder="Paket teslim edilecek adres (tam adres bilgisi)"
                  rows="3"
                />
              </div>
            </div>
          </div>

          {/* Package Details */}
          <PackageDetailsForm
            packageDetails={packageDetails}
            setPackageDetails={setPackageDetails}
          />

          {/* Recipient Info */}
          <Card>
            <CardHeader>
              <CardTitle>Alıcı Bilgileri</CardTitle>
            </CardHeader>
            <CardContent className="grid md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="recipient-name">Alıcı Adı Soyadı</Label>
                <Input
                  id="recipient-name"
                  placeholder="Ahmet Yılmaz"
                  value={recipientInfo.name}
                  onChange={(e) => setRecipientInfo({
                    ...recipientInfo,
                    name: e.target.value
                  })}
                  required
                  data-testid="recipient-name"
                />
              </div>
              
              <div>
                <Label htmlFor="recipient-phone">Alıcı Telefonu</Label>
                <Input
                  id="recipient-phone"
                  type="tel"
                  placeholder="+90 5XX XXX XX XX"
                  value={recipientInfo.phone}
                  onChange={(e) => setRecipientInfo({
                    ...recipientInfo,
                    phone: e.target.value
                  })}
                  required
                  data-testid="recipient-phone"
                />
              </div>
            </CardContent>
          </Card>

          {/* Order Notes */}
          <div>
            <Label htmlFor="order-notes">Sipariş Notları (Opsiyonel)</Label>
            <Textarea
              id="order-notes"
              placeholder="Kurye için ek bilgiler..."
              value={orderNotes}
              onChange={(e) => setOrderNotes(e.target.value)}
              data-testid="order-notes"
            />
          </div>

          {/* Pricing */}
          {pricing && (
            <PricingDisplay pricing={pricing} packageDetails={packageDetails} />
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              type="submit"
              disabled={loading || !pricing}
              className="flex-1 bg-orange-600 hover:bg-orange-700"
              data-testid="create-package-order-btn"
            >
              {loading ? 'Oluşturuluyor...' : `Paket Gönder (₺${pricing?.total_delivery_fee?.toFixed(2) || '0.00'})`}
            </Button>
            <Button
              type="button"
              onClick={onCancel}
              variant="outline"
              className="flex-1"
            >
              İptal
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

// Package Order History Component
export const PackageOrderHistory = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPackageOrders();
  }, []);

  const fetchPackageOrders = async () => {
    try {
      const token = localStorage.getItem('delivertr_token');
      const response = await axios.get(`${API}/orders/my-orders`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Filter only package orders
      const packageOrders = response.data.orders.filter(order => order.order_type === 'package');
      setOrders(packageOrders);
    } catch (error) {
      console.error('Paket siparişleri alınamadı:', error);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Paket siparişleri yükleniyor...</p>
        </CardContent>
      </Card>
    );
  }

  if (orders.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <div className="text-4xl mb-4">📦</div>
          <p className="text-gray-500">Henüz paket göndermediniz</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {orders.map((order) => (
        <Card key={order.id} className="hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <div className="flex justify-between items-start mb-3">
              <div>
                <h3 className="font-semibold">Paket #{order.id.substring(0, 8)}</h3>
                <p className="text-sm text-gray-600">
                  {new Date(order.created_at).toLocaleString('tr-TR')}
                </p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-lg">₺{order.total?.toFixed(2)}</p>
                <Badge className="mt-1">
                  {order.package_details?.priority === 'express' ? '⚡ Express' : '📦 Normal'}
                </Badge>
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <p><strong>Alıcı:</strong> {order.recipient_name}</p>
              <p><strong>Telefon:</strong> {order.recipient_phone}</p>
              <p><strong>Alış:</strong> {order.pickup_location?.address}</p>
              <p><strong>Teslim:</strong> {order.delivery_location?.address}</p>
              
              {order.package_details && (
                <div className="mt-3 p-2 bg-gray-50 rounded">
                  <p className="text-xs text-gray-600">
                    <strong>Paket:</strong> {order.package_details.weight_kg}kg
                    {order.package_details.dimensions && ` • ${order.package_details.dimensions}`}
                    {order.package_details.is_fragile && ' • Kırılabilir'}
                    {order.package_details.requires_cold_chain && ' • Soğuk zincir'}
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-between items-center mt-4">
              <Badge 
                className={`${
                  order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                  order.status === 'delivering' ? 'bg-blue-100 text-blue-800' :
                  order.status === 'picked_up' ? 'bg-purple-100 text-purple-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}
              >
                {order.status === 'delivered' && '✅ Teslim Edildi'}
                {order.status === 'delivering' && '🚚 Yolda'}
                {order.status === 'picked_up' && '📦 Alındı'}
                {order.status === 'pending' && '⏳ Beklemede'}
              </Badge>
              
              <Button variant="outline" size="sm">
                Detaylar
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default CreatePackageOrder;