import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { History, Filter, ChevronLeft, ChevronRight, Package, MapPin, Calendar } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://quickship-49.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

const STATUS_LABELS = {
  'picked_up': { label: 'Alındı', color: 'bg-blue-600' },
  'delivering': { label: 'Yolda', color: 'bg-yellow-600' },
  'delivered': { label: 'Teslim Edildi', color: 'bg-green-600' },
  'cancelled': { label: 'İptal', color: 'bg-red-600' }
};

export const CourierOrderHistoryFiltered = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    size: 10,
    total: 0,
    pages: 0
  });

  // Filters
  const [filters, setFilters] = useState({
    status: '',
    from_date: '',
    to_date: '',
    business: '',
    city: '',
    sort: 'createdAt:desc'
  });

  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchOrderHistory();
  }, [pagination.page, filters]);

  const fetchOrderHistory = async () => {
    try {
      setLoading(true);

      // Build query string
      const params = new URLSearchParams();
      params.append('page', pagination.page);
      params.append('size', pagination.size);
      
      if (filters.status) params.append('status', filters.status);
      if (filters.from_date) params.append('from_date', filters.from_date);
      if (filters.to_date) params.append('to_date', filters.to_date);
      if (filters.business) params.append('business', filters.business);
      if (filters.city) params.append('city', filters.city);
      if (filters.sort) params.append('sort', filters.sort);

      const response = await fetch(`${API}/courier/orders/history?${params.toString()}`, {
        method: 'GET',
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setOrders(data.orders);
          setPagination(prev => ({
            ...prev,
            total: data.pagination.total,
            pages: data.pagination.pages
          }));
        }
      } else {
        toast.error('Sipariş geçmişi yüklenemedi');
      }
    } catch (error) {
      console.error('Sipariş geçmişi hatası:', error);
      toast.error('Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
    setPagination(prev => ({ ...prev, page: 1 })); // Reset to first page
  };

  const clearFilters = () => {
    setFilters({
      status: '',
      from_date: '',
      to_date: '',
      business: '',
      city: '',
      sort: 'createdAt:desc'
    });
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const goToPage = (page) => {
    if (page >= 1 && page <= pagination.pages) {
      setPagination(prev => ({ ...prev, page }));
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Sipariş Geçmişi
              </CardTitle>
              <CardDescription>
                Toplam {pagination.total} sipariş
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4 mr-2" />
              {showFilters ? 'Filtreleri Gizle' : 'Filtrele'}
            </Button>
          </div>
        </CardHeader>

        {/* Filters Panel */}
        {showFilters && (
          <CardContent className="border-t">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              {/* Status Filter */}
              <div className="space-y-2">
                <Label htmlFor="statusFilter">Durum</Label>
                <Select
                  value={filters.status}
                  onValueChange={(value) => handleFilterChange('status', value)}
                >
                  <SelectTrigger id="statusFilter">
                    <SelectValue placeholder="Tümü" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Tümü</SelectItem>
                    <SelectItem value="picked_up">Alındı</SelectItem>
                    <SelectItem value="delivering">Yolda</SelectItem>
                    <SelectItem value="delivered">Teslim Edildi</SelectItem>
                    <SelectItem value="cancelled">İptal</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Date From */}
              <div className="space-y-2">
                <Label htmlFor="fromDate">Başlangıç Tarihi</Label>
                <Input
                  id="fromDate"
                  type="date"
                  value={filters.from_date}
                  onChange={(e) => handleFilterChange('from_date', e.target.value)}
                />
              </div>

              {/* Date To */}
              <div className="space-y-2">
                <Label htmlFor="toDate">Bitiş Tarihi</Label>
                <Input
                  id="toDate"
                  type="date"
                  value={filters.to_date}
                  onChange={(e) => handleFilterChange('to_date', e.target.value)}
                />
              </div>

              {/* Business Name */}
              <div className="space-y-2">
                <Label htmlFor="businessFilter">İşletme Adı</Label>
                <Input
                  id="businessFilter"
                  placeholder="İşletme ara..."
                  value={filters.business}
                  onChange={(e) => handleFilterChange('business', e.target.value)}
                />
              </div>

              {/* City */}
              <div className="space-y-2">
                <Label htmlFor="cityFilter">Şehir</Label>
                <Input
                  id="cityFilter"
                  placeholder="Şehir ara..."
                  value={filters.city}
                  onChange={(e) => handleFilterChange('city', e.target.value)}
                />
              </div>

              {/* Sort */}
              <div className="space-y-2">
                <Label htmlFor="sortFilter">Sıralama</Label>
                <Select
                  value={filters.sort}
                  onValueChange={(value) => handleFilterChange('sort', value)}
                >
                  <SelectTrigger id="sortFilter">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="createdAt:desc">Yeni → Eski</SelectItem>
                    <SelectItem value="createdAt:asc">Eski → Yeni</SelectItem>
                    <SelectItem value="total_amount:desc">Tutar (Yüksek → Düşük)</SelectItem>
                    <SelectItem value="total_amount:asc">Tutar (Düşük → Yüksek)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Button variant="outline" size="sm" onClick={clearFilters}>
              Filtreleri Temizle
            </Button>
          </CardContent>
        )}
      </Card>

      {/* Orders List */}
      {loading ? (
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          </CardContent>
        </Card>
      ) : orders.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-muted-foreground">
              <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Sipariş bulunamadı</p>
              <p className="text-sm mt-2">Filtrelerinizi değiştirmeyi deneyin</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {orders.map((order) => (
            <Card key={order.id}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold">{order.business_name}</h3>
                      <Badge className={STATUS_LABELS[order.status]?.color || 'bg-gray-600'}>
                        {STATUS_LABELS[order.status]?.label || order.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-1">
                      {order.business_address}
                    </p>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      {formatDate(order.created_at)}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold">₺{order.total_amount?.toFixed(2) || '0.00'}</p>
                    <p className="text-sm text-green-600">
                      Kazanç: ₺{order.courier_earning?.toFixed(2) || '0.00'}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-2 text-sm">
                  <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    {order.delivery_address?.text || 'Adres bilgisi yok'}
                  </span>
                </div>

                {order.items && order.items.length > 0 && (
                  <div className="mt-3 pt-3 border-t">
                    <p className="text-xs text-muted-foreground">
                      {order.items.length} ürün: {order.items.map(item => item.name).join(', ')}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pagination.pages > 1 && (
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Sayfa {pagination.page} / {pagination.pages}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => goToPage(pagination.page - 1)}
                  disabled={pagination.page === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => goToPage(pagination.page + 1)}
                  disabled={pagination.page === pagination.pages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
