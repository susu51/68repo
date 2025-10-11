import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Badge } from './components/ui/badge';
import { Textarea } from './components/ui/textarea';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// File Upload Component for Menu Items
const MenuImageUpload = ({ onImageSelect, currentImage }) => {
  const [uploading, setUploading] = useState(false);
  const [imageUrl, setImageUrl] = useState(currentImage || '');

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setImageUrl(response.data.file_url);
      onImageSelect(response.data.file_url);
      toast.success('Fotoğraf yüklendi');
    } catch (error) {
      toast.error('Fotoğraf yükleme başarısız');
    }
    setUploading(false);
  };

  return (
    <div className="space-y-2">
      <Label>Ürün Fotoğrafı</Label>
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
          id="menu-image-upload"
        />
        <label htmlFor="menu-image-upload" className="cursor-pointer">
          {uploading ? (
            <div className="text-blue-600">Yükleniyor...</div>
          ) : imageUrl ? (
            <div className="space-y-2">
              <img src={`${BACKEND_URL}${imageUrl}`} alt="Preview" className="mx-auto max-h-32 rounded" />
              <p className="text-green-600 text-sm">✓ Fotoğraf yüklendi</p>
            </div>
          ) : (
            <div className="text-gray-500">
              📷 Ürün fotoğrafı seçin
            </div>
          )}
        </label>
      </div>
    </div>
  );
};

// Create Category Modal
export const CreateCategoryModal = ({ isOpen, onClose, onCategoryCreated }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const response = await axios.post(`${API}/menu/category`, formData, {
        withCredentials: true
      });

      toast.success('Kategori oluşturuldu!');
      setFormData({ name: '', description: '' });
      onCategoryCreated();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Kategori oluşturulamadı');
    }
    setLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md mx-4">
        <CardHeader>
          <CardTitle>Yeni Kategori</CardTitle>
          <CardDescription>Menü kategorisi oluşturun</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="category-name">Kategori Adı</Label>
              <Input
                id="category-name"
                placeholder="Örn: Ana Yemekler, İçecekler"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
                data-testid="category-name-input"
              />
            </div>
            
            <div>
              <Label htmlFor="category-description">Açıklama (Opsiyonel)</Label>
              <Textarea
                id="category-description"
                placeholder="Kategori açıklaması"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                data-testid="category-description-input"
              />
            </div>
            
            <div className="flex gap-3">
              <Button
                type="submit"
                disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-700"
                data-testid="create-category-btn"
              >
                {loading ? 'Oluşturuluyor...' : 'Kategori Oluştur'}
              </Button>
              <Button
                type="button"
                onClick={onClose}
                variant="outline"
                className="flex-1"
              >
                İptal
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

// Create Menu Item Modal
export const CreateMenuItemModal = ({ isOpen, onClose, categories, onItemCreated }) => {
  const [formData, setFormData] = useState({
    category_id: '',
    name: '',
    description: '',
    price: '',
    preparation_time_minutes: 15,
    ingredients: '',
    allergens: '',
    tags: ''
  });
  const [imageUrl, setImageUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      
      const submitData = {
        ...formData,
        price: parseFloat(formData.price),
        image_url: imageUrl,
        ingredients: formData.ingredients ? formData.ingredients.split(',').map(i => i.trim()) : [],
        allergens: formData.allergens ? formData.allergens.split(',').map(i => i.trim()) : [],
        tags: formData.tags ? formData.tags.split(',').map(i => i.trim()) : []
      };

      const response = await axios.post(`${API}/menu/item`, submitData, {
        withCredentials: true
      });

      toast.success('Ürün eklendi!');
      setFormData({
        category_id: '',
        name: '',
        description: '',
        price: '',
        preparation_time_minutes: 15,
        ingredients: '',
        allergens: '',
        tags: ''
      });
      setImageUrl('');
      onItemCreated();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ürün eklenemedi');
    }
    setLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <CardTitle>Yeni Ürün Ekle</CardTitle>
          <CardDescription>Menünüze yeni ürün ekleyin</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="item-category">Kategori</Label>
                <Select 
                  onValueChange={(value) => setFormData({...formData, category_id: value})} 
                  required
                >
                  <SelectTrigger data-testid="item-category-select">
                    <SelectValue placeholder="Kategori seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((category) => (
                      <SelectItem key={category.id} value={category.id}>
                        {category.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label htmlFor="item-price">Fiyat (₺)</Label>
                <Input
                  id="item-price"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="25.50"
                  value={formData.price}
                  onChange={(e) => setFormData({...formData, price: e.target.value})}
                  required
                  data-testid="item-price-input"
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="item-name">Ürün Adı</Label>
              <Input
                id="item-name"
                placeholder="Örn: Margarita Pizza, Köfte Tabağı"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
                data-testid="item-name-input"
              />
            </div>
            
            <div>
              <Label htmlFor="item-description">Açıklama</Label>
              <Textarea
                id="item-description"
                placeholder="Ürün açıklaması, malzemeleri, özel notlar..."
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                data-testid="item-description-input"
              />
            </div>
            
            <div>
              <MenuImageUpload
                onImageSelect={setImageUrl}
                currentImage={imageUrl}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="prep-time">Hazırlanma Süresi (dk)</Label>
                <Input
                  id="prep-time"
                  type="number"
                  min="1"
                  max="120"
                  value={formData.preparation_time_minutes}
                  onChange={(e) => setFormData({...formData, preparation_time_minutes: parseInt(e.target.value)})}
                  data-testid="prep-time-input"
                />
              </div>
              
              <div>
                <Label htmlFor="item-tags">Etiketler (virgülle ayırın)</Label>
                <Input
                  id="item-tags"
                  placeholder="vejetaryen, acılı, popüler"
                  value={formData.tags}
                  onChange={(e) => setFormData({...formData, tags: e.target.value})}
                  data-testid="item-tags-input"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="ingredients">Malzemeler (virgülle ayırın)</Label>
                <Input
                  id="ingredients"
                  placeholder="domates, mozzarella, fesleğen"
                  value={formData.ingredients}
                  onChange={(e) => setFormData({...formData, ingredients: e.target.value})}
                  data-testid="ingredients-input"
                />
              </div>
              
              <div>
                <Label htmlFor="allergens">Alerjenler (virgülle ayırın)</Label>
                <Input
                  id="allergens"
                  placeholder="süt, gluten, yumurta"
                  value={formData.allergens}
                  onChange={(e) => setFormData({...formData, allergens: e.target.value})}
                  data-testid="allergens-input"
                />
              </div>
            </div>
            
            <div className="flex gap-3">
              <Button
                type="submit"
                disabled={loading}
                className="flex-1 bg-green-600 hover:bg-green-700"
                data-testid="create-item-btn"
              >
                {loading ? 'Ekleniyor...' : 'Ürün Ekle'}
              </Button>
              <Button
                type="button"
                onClick={onClose}
                variant="outline"
                className="flex-1"
              >
                İptal
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

// Menu Display Component
export const MenuDisplay = ({ businessId, isOwner = false }) => {
  const [menu, setMenu] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMenu();
  }, [businessId]);

  const fetchMenu = async () => {
    try {
      const endpoint = isOwner ? '/menu/my-menu' : `/menu/business/${businessId}`;
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      
      const response = await axios.get(`${API}${endpoint}`, {
        headers: isOwner ? { Authorization: `Bearer ${token}` } : {}
      });
      
      setMenu(response.data.menu);
    } catch (error) {
      console.error('Menü yüklenemedi:', error);
      toast.error('Menü yüklenemedi');
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Menü yükleniyor...</p>
        </CardContent>
      </Card>
    );
  }

  if (menu.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <div className="text-4xl mb-4">🍽️</div>
          <p className="text-gray-500">
            {isOwner ? 'Henüz menünüze ürün eklememişsiniz' : 'Bu işletmenin menüsü henüz hazırlanmamış'}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" data-testid="menu-display">
      {menu.map((category) => (
        <Card key={category.id}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {category.name}
              <Badge variant="outline">{category.items.length} ürün</Badge>
            </CardTitle>
            {category.description && (
              <CardDescription>{category.description}</CardDescription>
            )}
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {category.items.map((item) => (
                <Card key={item.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    {item.image_url && (
                      <img 
                        src={`${BACKEND_URL}${item.image_url}`} 
                        alt={item.name}
                        className="w-full h-32 object-cover rounded-lg mb-3"
                      />
                    )}
                    
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <h3 className="font-semibold">{item.name}</h3>
                        <span className="font-bold text-green-600">₺{item.price}</span>
                      </div>
                      
                      {item.description && (
                        <p className="text-sm text-gray-600">{item.description}</p>
                      )}
                      
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>🕒 {item.preparation_time_minutes} dk</span>
                      </div>
                      
                      {item.tags && item.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {item.tags.map((tag, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                      
                      {!isOwner && (
                        <Button 
                          className="w-full bg-green-600 hover:bg-green-700" 
                          size="sm"
                          data-testid={`add-to-cart-${item.id}`}
                        >
                          Sepete Ekle
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

// Main Menu Management Component
export const MenuManagement = () => {
  const [menu, setMenu] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateCategory, setShowCreateCategory] = useState(false);
  const [showCreateItem, setShowCreateItem] = useState(false);

  useEffect(() => {
    fetchMenu();
  }, []);

  const fetchMenu = async () => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const response = await axios.get(`${API}/menu/my-menu`, {
        withCredentials: true
      });
      
      setMenu(response.data.menu);
    } catch (error) {
      console.error('Menü yüklenemedi:', error);
    }
    setLoading(false);
  };

  const categories = menu.map(category => ({
    id: category.id,
    name: category.name
  }));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Menü Yönetimi</h2>
          <p className="text-gray-600">Menünüzü oluşturun ve yönetin</p>
        </div>
        
        <div className="flex gap-2">
          <Button
            onClick={() => setShowCreateCategory(true)}
            variant="outline"
            data-testid="create-category-btn"
          >
            + Kategori
          </Button>
          <Button
            onClick={() => setShowCreateItem(true)}
            disabled={categories.length === 0}
            className="bg-green-600 hover:bg-green-700"
            data-testid="create-item-btn"
          >
            + Ürün Ekle
          </Button>
        </div>
      </div>

      {categories.length === 0 && !loading && (
        <Card>
          <CardContent className="text-center py-12">
            <div className="text-4xl mb-4">📋</div>
            <p className="text-gray-500 mb-4">Önce bir kategori oluşturun</p>
            <Button 
              onClick={() => setShowCreateCategory(true)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              İlk Kategoriyi Oluştur
            </Button>
          </CardContent>
        </Card>
      )}

      <MenuDisplay businessId="" isOwner={true} />

      <CreateCategoryModal
        isOpen={showCreateCategory}
        onClose={() => setShowCreateCategory(false)}
        onCategoryCreated={fetchMenu}
      />

      <CreateMenuItemModal
        isOpen={showCreateItem}
        onClose={() => setShowCreateItem(false)}
        categories={categories}
        onItemCreated={fetchMenu}
      />
    </div>
  );
};

export default MenuManagement;