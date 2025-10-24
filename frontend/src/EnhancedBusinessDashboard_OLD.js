import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Label } from "./components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Textarea } from "./components/ui/textarea";
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const EnhancedBusinessDashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  
  // Restaurant view data
  const [restaurantView, setRestaurantView] = useState(null);
  const [featuredStatus, setFeaturedStatus] = useState(null);
  const [categories, setCategories] = useState({});
  
  // Product management
  const [products, setProducts] = useState([]);
  const [showProductForm, setShowProductForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [productForm, setProductForm] = useState({
    name: '',
    category: '',
    price: '',
    description: '',
    preparation_time_minutes: 15,
    is_available: true
  });

  // Featured promotion
  const [selectedPlan, setSelectedPlan] = useState('');
  const [showFeaturedModal, setShowFeaturedModal] = useState(false);

  // Fetch restaurant public view
  const fetchRestaurantView = async () => {
    try {
      const response = await axios.get(`${API}/business/restaurant-view`);
      setRestaurantView(response.data);
    } catch (error) {
      console.error('Failed to fetch restaurant view:', error);
    }
  };

  // Fetch featured status
  const fetchFeaturedStatus = async () => {
    try {
      const response = await axios.get(`${API}/business/featured-status`);
      setFeaturedStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch featured status:', error);
    }
  };

  // Fetch product categories
  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/business/products/categories`);
      setCategories(response.data);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  // Fetch products
  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`);
      setProducts(response.data || []);
    } catch (error) {
      console.error('Failed to fetch products:', error);
    }
  };

  // Handle featured promotion request
  const requestFeaturedPromotion = async () => {
    if (!selectedPlan) {
      toast.error('Lütfen bir plan seçin');
      return;
    }

    try {
      setLoading(true);
      await axios.post(`${API}/business/request-featured`, {
        plan: selectedPlan
      });
      
      toast.success('Öne çıkarma talebiniz gönderildi!');
      setShowFeaturedModal(false);
      fetchFeaturedStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Talep gönderilemedi');
    }
    setLoading(false);
  };

  // Handle product form submission
  const handleProductSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const productData = {
        ...productForm,
        price: parseFloat(productForm.price)
      };

      if (editingProduct) {
        await axios.put(`${API}/products/${editingProduct.id}`, productData);
        toast.success('Ürün güncellendi!');
      } else {
        await axios.post(`${API}/products`, productData);
        toast.success('Ürün eklendi!');
      }

      setShowProductForm(false);
      setEditingProduct(null);
      setProductForm({
        name: '',
        category: '',
        price: '',
        description: '',
        preparation_time_minutes: 15,
        is_available: true
      });
      
      fetchProducts();
      fetchCategories();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ürün kaydedilemedi');
    }
    setLoading(false);
  };

  // Handle product deletion
  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('Bu ürünü silmek istediğinizden emin misiniz?')) return;

    try {
      await axios.delete(`${API}/products/${productId}`);
      toast.success('Ürün silindi!');
      fetchProducts();
      fetchCategories();
    } catch (error) {
      toast.error('Ürün silinemedi');
    }
  };

  // Open restaurant in new tab
  const openRestaurantView = () => {
    const restaurantUrl = `${window.location.origin}/restaurant/${user.id}`;
    window.open(restaurantUrl, '_blank');
  };

  useEffect(() => {
    fetchRestaurantView();
    fetchFeaturedStatus();
    fetchCategories();
    fetchProducts();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50">
      {/* Header */}
      <div className="bg-white/70 backdrop-blur-lg border-b border-gray-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="text-2xl">🏪</div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">İşletme Paneli</h1>
                <p className="text-sm text-gray-600">
                  {user?.business_name || 'İşletmeniz'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Featured Badge */}
              {featuredStatus?.is_featured && (
                <Badge className="bg-yellow-500 text-white">
                  ⭐ Öne Çıkan
                </Badge>
              )}
              
              {/* Restaurant Actions */}
              <Button onClick={openRestaurantView} variant="outline">
                👁️ Restoranımı Görüntüle
              </Button>
              
              <Button onClick={onLogout} variant="outline">
                Çıkış
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-3xl mb-2">🍽️</div>
              <div className="text-2xl font-bold text-blue-600">
                {products.length}
              </div>
              <div className="text-sm text-gray-600">Toplam Ürün</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-3xl mb-2">⭐</div>
              <div className="text-2xl font-bold text-yellow-600">
                {restaurantView?.business_info?.average_rating || 'N/A'}
              </div>
              <div className="text-sm text-gray-600">Ortalama Puan</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-3xl mb-2">📊</div>
              <div className="text-2xl font-bold text-green-600">
                {restaurantView?.business_info?.total_ratings || 0}
              </div>
              <div className="text-sm text-gray-600">Toplam Değerlendirme</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-3xl mb-2">🎯</div>
              <div className="text-2xl font-bold text-purple-600">
                {featuredStatus?.is_featured ? 'Aktif' : 'Pasif'}
              </div>
              <div className="text-sm text-gray-600">Öne Çıkarma</div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs Navigation */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">📊 Genel Bakış</TabsTrigger>
            <TabsTrigger value="products">🍽️ Ürünler</TabsTrigger>
            <TabsTrigger value="featured">⭐ Öne Çıkar</TabsTrigger>
            <TabsTrigger value="reviews">💬 Yorumlar</TabsTrigger>
            <TabsTrigger value="settings">⚙️ Ayarlar</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Restaurant Info */}
              <Card>
                <CardHeader>
                  <CardTitle>Restoran Bilgileri</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <span className="font-medium">İşletme Adı:</span>
                      <p className="text-gray-600">{restaurantView?.business_info?.business_name}</p>
                    </div>
                    <div>
                      <span className="font-medium">Açıklama:</span>
                      <p className="text-gray-600">{restaurantView?.business_info?.description}</p>
                    </div>
                    <div>
                      <span className="font-medium">Adres:</span>
                      <p className="text-gray-600">{restaurantView?.business_info?.address}</p>
                    </div>
                    <div>
                      <span className="font-medium">Kategori:</span>
                      <p className="text-gray-600">{restaurantView?.business_info?.business_category}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card>
                <CardHeader>
                  <CardTitle>Son Yorumlar</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {restaurantView?.recent_reviews?.slice(0, 3).map((review, index) => (
                      <div key={index} className="border-b pb-2 last:border-b-0">
                        <div className="flex items-center space-x-2">
                          <div className="text-yellow-500">
                            {'⭐'.repeat(review.rating)}
                          </div>
                          <span className="text-sm text-gray-500">
                            {new Date(review.created_at).toLocaleDateString('tr-TR')}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">
                          {review.comment || 'Yorum yok'}
                        </p>
                      </div>
                    )) || (
                      <p className="text-gray-500 text-center py-4">Henüz yorum yok</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Products Tab */}
          <TabsContent value="products" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Ürün Yönetimi</h2>
              <Button onClick={() => setShowProductForm(true)}>
                ➕ Yeni Ürün Ekle
              </Button>
            </div>

            {/* Product Categories Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl mb-2">🍕</div>
                  <div className="font-semibold">Yiyecek</div>
                  <div className="text-sm text-gray-600">
                    {categories.food_categories?.length || 0} kategori
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl mb-2">🥤</div>
                  <div className="font-semibold">İçecek</div>
                  <div className="text-sm text-gray-600">
                    {categories.drink_categories?.length || 0} kategori
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl mb-2">📊</div>
                  <div className="font-semibold">Toplam</div>
                  <div className="text-sm text-gray-600">
                    {categories.total_products || 0} ürün
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Product List */}
            <div className="space-y-4">
              {products.map((product) => (
                <Card key={product.id}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h4 className="font-semibold">{product.name}</h4>
                          <Badge variant={product.is_available ? 'default' : 'secondary'}>
                            {product.is_available ? 'Mevcut' : 'Tükendi'}
                          </Badge>
                          <Badge variant="outline">{product.category}</Badge>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{product.description}</p>
                        <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                          <span>💰 ₺{product.price}</span>
                          <span>⏱️ {product.preparation_time_minutes} dk</span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => {
                            setEditingProduct(product);
                            setProductForm({
                              name: product.name,
                              category: product.category,
                              price: product.price.toString(),
                              description: product.description,
                              preparation_time_minutes: product.preparation_time_minutes,
                              is_available: product.is_available
                            });
                            setShowProductForm(true);
                          }}
                        >
                          ✏️
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleDeleteProduct(product.id)}
                        >
                          🗑️
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Product Form Modal */}
            {showProductForm && (
              <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                <Card className="w-full max-w-md">
                  <CardHeader>
                    <CardTitle>
                      {editingProduct ? 'Ürünü Düzenle' : 'Yeni Ürün Ekle'}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleProductSubmit} className="space-y-4">
                      <div>
                        <Label htmlFor="name">Ürün Adı</Label>
                        <Input
                          id="name"
                          value={productForm.name}
                          onChange={(e) => setProductForm({...productForm, name: e.target.value})}
                          required
                        />
                      </div>
                      
                      <div>
                        <Label htmlFor="category">Kategori</Label>
                        <Input
                          id="category"
                          value={productForm.category}
                          onChange={(e) => setProductForm({...productForm, category: e.target.value})}
                          placeholder="Örn: pizza, burger, içecek"
                          required
                        />
                      </div>
                      
                      <div>
                        <Label htmlFor="price">Fiyat (₺)</Label>
                        <Input
                          id="price"
                          type="number"
                          step="0.01"
                          value={productForm.price}
                          onChange={(e) => setProductForm({...productForm, price: e.target.value})}
                          required
                        />
                      </div>
                      
                      <div>
                        <Label htmlFor="description">Açıklama</Label>
                        <Textarea
                          id="description"
                          value={productForm.description}
                          onChange={(e) => setProductForm({...productForm, description: e.target.value})}
                          placeholder="Ürün açıklaması..."
                        />
                      </div>
                      
                      <div>
                        <Label htmlFor="prep_time">Hazırlık Süresi (dakika)</Label>
                        <Input
                          id="prep_time"
                          type="number"
                          value={productForm.preparation_time_minutes}
                          onChange={(e) => setProductForm({...productForm, preparation_time_minutes: parseInt(e.target.value)})}
                          min="1"
                          max="120"
                        />
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="available"
                          checked={productForm.is_available}
                          onChange={(e) => setProductForm({...productForm, is_available: e.target.checked})}
                        />
                        <Label htmlFor="available">Mevcut</Label>
                      </div>
                      
                      <div className="flex space-x-2">
                        <Button type="submit" disabled={loading} className="flex-1">
                          {loading ? 'Kaydediliyor...' : (editingProduct ? 'Güncelle' : 'Ekle')}
                        </Button>
                        <Button 
                          type="button" 
                          variant="outline" 
                          onClick={() => {
                            setShowProductForm(false);
                            setEditingProduct(null);
                          }}
                          className="flex-1"
                        >
                          İptal
                        </Button>
                      </div>
                    </form>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* Featured Tab */}
          <TabsContent value="featured" className="space-y-6">
            <h2 className="text-2xl font-bold">Öne Çıkarma Sistemi</h2>
            
            {featuredStatus?.is_featured ? (
              <Card className="border-yellow-200 bg-yellow-50">
                <CardContent className="p-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="text-3xl">⭐</div>
                    <div>
                      <h3 className="text-xl font-bold text-yellow-800">
                        Restoranınız Öne Çıkan!
                      </h3>
                      <p className="text-yellow-700">
                        {featuredStatus.plan} planı ile öne çıkıyorsunuz
                      </p>
                    </div>
                  </div>
                  
                  <div className="bg-yellow-100 rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Süre:</span>
                        <p>{featuredStatus.remaining_days} gün kaldı</p>
                      </div>
                      <div>
                        <span className="font-medium">Bitiş Tarihi:</span>
                        <p>{new Date(featuredStatus.expires_at).toLocaleDateString('tr-TR')}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-4 text-sm text-yellow-700">
                    <p>✅ Müşteri listesinde en üstte görünüyorsunuz</p>
                    <p>✅ Restoran kartınızda "Öne Çıkan" rozeti var</p>
                    <p>✅ Banner alanlarında öncelikli yerdesiniz</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Restoranınızı Öne Çıkarın</CardTitle>
                    <CardDescription>
                      Daha fazla müşteriye ulaşmak için restoranınızı öne çıkarabilirsiniz
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {featuredStatus?.available_plans?.map((plan) => (
                        <Card 
                          key={plan.id} 
                          className={`cursor-pointer transition-all ${
                            selectedPlan === plan.id ? 'border-blue-500 bg-blue-50' : 'hover:shadow-md'
                          }`}
                          onClick={() => setSelectedPlan(plan.id)}
                        >
                          <CardContent className="p-4 text-center">
                            <div className="text-2xl mb-2">
                              {plan.id === 'daily' ? '📅' : plan.id === 'weekly' ? '📆' : '🗓️'}
                            </div>
                            <h4 className="font-bold text-lg">{plan.name}</h4>
                            <div className="text-2xl font-bold text-green-600 my-2">
                              ₺{plan.price}
                            </div>
                            <p className="text-sm text-gray-600">
                              {plan.duration_days} gün öne çıkarma
                            </p>
                            <div className="mt-3 text-xs text-gray-500">
                              Günlük ₺{(plan.price / plan.duration_days).toFixed(2)}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                    
                    {selectedPlan && (
                      <div className="mt-6 text-center">
                        <Button 
                          onClick={() => setShowFeaturedModal(true)}
                          className="bg-yellow-600 hover:bg-yellow-700 text-white px-8 py-3"
                        >
                          ⭐ Öne Çıkarma Talebinde Bulun
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader>
                    <CardTitle>Öne Çıkarma Avantajları</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-green-600">✅</span>
                          <span>Müşteri listesinde en üstte görünme</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-green-600">✅</span>
                          <span>"Öne Çıkan" rozeti</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-green-600">✅</span>
                          <span>Banner alanlarında öncelik</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-green-600">✅</span>
                          <span>Daha fazla görünürlük</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Featured Request Modal */}
            {showFeaturedModal && (
              <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                <Card className="w-full max-w-md">
                  <CardHeader>
                    <CardTitle>Öne Çıkarma Talebi</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <p>
                        <strong>{featuredStatus?.available_plans?.find(p => p.id === selectedPlan)?.name}</strong> planını seçtiniz.
                      </p>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <div className="flex justify-between">
                          <span>Plan:</span>
                          <span className="font-medium">
                            {featuredStatus?.available_plans?.find(p => p.id === selectedPlan)?.name}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Süre:</span>
                          <span className="font-medium">
                            {featuredStatus?.available_plans?.find(p => p.id === selectedPlan)?.duration_days} gün
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Ücret:</span>
                          <span className="font-bold text-green-600">
                            ₺{featuredStatus?.available_plans?.find(p => p.id === selectedPlan)?.price}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600">
                        Talebiniz admin onayından sonra aktif olacaktır.
                      </p>
                      <div className="flex space-x-2">
                        <Button 
                          onClick={requestFeaturedPromotion}
                          disabled={loading}
                          className="flex-1"
                        >
                          {loading ? 'Gönderiliyor...' : 'Talep Gönder'}
                        </Button>
                        <Button 
                          variant="outline"
                          onClick={() => setShowFeaturedModal(false)}
                          className="flex-1"
                        >
                          İptal
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* Reviews Tab */}
          <TabsContent value="reviews" className="space-y-6">
            <h2 className="text-2xl font-bold">Müşteri Yorumları</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-1">
                <CardHeader>
                  <CardTitle>Puan Özeti</CardTitle>
                </CardHeader>
                <CardContent className="text-center">
                  <div className="text-4xl font-bold text-yellow-600 mb-2">
                    {restaurantView?.business_info?.average_rating || 'N/A'}
                  </div>
                  <div className="text-yellow-500 text-2xl mb-2">
                    {'⭐'.repeat(Math.floor(restaurantView?.business_info?.average_rating || 0))}
                  </div>
                  <p className="text-gray-600">
                    {restaurantView?.business_info?.total_ratings || 0} değerlendirme
                  </p>
                </CardContent>
              </Card>
              
              <div className="lg:col-span-2 space-y-4">
                {restaurantView?.recent_reviews?.map((review, index) => (
                  <Card key={index}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-yellow-500">
                          {'⭐'.repeat(review.rating)}
                        </div>
                        <span className="text-sm text-gray-500">
                          {new Date(review.created_at).toLocaleDateString('tr-TR')}
                        </span>
                      </div>
                      <p className="text-gray-700">
                        {review.comment || 'Müşteri yorum yazmamış'}
                      </p>
                    </CardContent>
                  </Card>
                )) || (
                  <Card>
                    <CardContent className="p-8 text-center">
                      <div className="text-4xl mb-4">💬</div>
                      <h3 className="text-lg font-semibold mb-2">Henüz Yorum Yok</h3>
                      <p className="text-gray-600">
                        İlk siparişleriniz teslim edildikten sonra müşteri yorumları burada görünecek.
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <h2 className="text-2xl font-bold">İşletme Ayarları</h2>
            
            <Card>
              <CardHeader>
                <CardTitle>Hesap Bilgileri</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>E-posta</Label>
                    <p className="text-gray-600">{user?.email}</p>
                  </div>
                  <div>
                    <Label>Telefon</Label>
                    <p className="text-gray-600">{user?.phone || 'Belirtilmemiş'}</p>
                  </div>
                  <div>
                    <Label>Şehir</Label>
                    <p className="text-gray-600">{user?.city}</p>
                  </div>
                  <div>
                    <Label>Durum</Label>
                    <Badge variant={user?.is_active ? 'default' : 'secondary'}>
                      {user?.is_active ? 'Aktif' : 'Pasif'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default EnhancedBusinessDashboard;