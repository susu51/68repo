import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { toast } from 'react-hot-toast';
import api from '../api/http';

const ContentEditor = () => {
  const [contentBlocks, setContentBlocks] = useState([]);
  const [selectedBlock, setSelectedBlock] = useState(null);
  const [loading, setLoading] = useState(false);
  const [editMode, setEditMode] = useState(false);

  // Load content blocks on component mount
  useEffect(() => {
    loadContentBlocks();
  }, []);

  const loadContentBlocks = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/content/blocks');
      setContentBlocks(response.data || []);
    } catch (error) {
      console.error('Error loading content blocks:', error);
      toast.error('İçerik blokları yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const saveContentBlock = async (blockData) => {
    try {
      setLoading(true);
      await apiClient.put(`/content/blocks/${blockData._id}`, blockData);
      toast.success('İçerik bloğu kaydedildi');
      await loadContentBlocks();
      setEditMode(false);
    } catch (error) {
      console.error('Error saving content block:', error);
      toast.error('İçerik bloğu kaydedilirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const PopularProductsEditor = ({ section, onUpdate }) => {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
      loadPopularProducts();
    }, []);

    const loadPopularProducts = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get('/content/popular-products?limit=20');
        setProducts(response.data || []);
      } catch (error) {
        console.error('Error loading popular products:', error);
        toast.error('Popüler ürünler yüklenirken hata oluştu');
      } finally {
        setLoading(false);
      }
    };

    const handleChange = (field, value) => {
      onUpdate({ ...section, [field]: value });
    };

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Başlık</Label>
            <Input
              value={section.title || ''}
              onChange={(e) => handleChange('title', e.target.value)}
              placeholder="Popüler Ürünler"
            />
          </div>
          <div>
            <Label>Gösterilecek Ürün Sayısı</Label>
            <Select 
              value={(section.limit || 8).toString()} 
              onValueChange={(value) => handleChange('limit', parseInt(value))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seçin" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="4">4 Ürün</SelectItem>
                <SelectItem value="6">6 Ürün</SelectItem>
                <SelectItem value="8">8 Ürün</SelectItem>
                <SelectItem value="10">10 Ürün</SelectItem>
                <SelectItem value="12">12 Ürün</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div>
          <Label>Sıralama Kriteri</Label>
          <Select 
            value={section.sort_by || 'order_count'} 
            onValueChange={(value) => handleChange('sort_by', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Sıralama" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="order_count">Sipariş Sayısına Göre</SelectItem>
              <SelectItem value="recent">En Yeni Siparişler</SelectItem>
              <SelectItem value="revenue">Gelire Göre</SelectItem>
              <SelectItem value="rating">Puana Göre</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label>Zaman Aralığı</Label>
          <Select 
            value={section.time_range || 'all_time'} 
            onValueChange={(value) => handleChange('time_range', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Zaman" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Bugün</SelectItem>
              <SelectItem value="week">Bu Hafta</SelectItem>
              <SelectItem value="month">Bu Ay</SelectItem>
              <SelectItem value="all_time">Tüm Zamanlar</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Live Preview */}
        <div className="border-t pt-4">
          <Label className="text-lg font-medium">🔍 Canlı Önizleme</Label>
          <div className="mt-2 p-4 bg-gray-50 rounded-lg">
            {loading ? (
              <div className="text-center py-4">
                <div className="animate-spin w-6 h-6 border-2 border-orange-600 border-t-transparent rounded-full mx-auto"></div>
                <div className="mt-2 text-sm text-gray-600">Ürünler yükleniyor...</div>
              </div>
            ) : (
              <div>
                <div className="font-medium mb-3 text-center">{section.title || 'Popüler Ürünler'}</div>
                <div className="grid grid-cols-2 gap-2">
                  {products.slice(0, section.limit || 8).map((product, i) => (
                    <div key={i} className="flex justify-between items-center p-2 bg-white rounded border text-sm">
                      <div>
                        <div className="font-medium text-gray-900">{product.name}</div>
                        <div className="text-xs text-gray-600">{product.business_name || 'Restaurant'}</div>
                      </div>
                      <div className="text-orange-600 font-bold text-xs">
                        #{i + 1}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="text-xs text-gray-500 text-center mt-2">
                  {section.limit || 8} ürün • {section.sort_by?.replace('_', ' ') || 'sipariş sayısı'} • {section.time_range?.replace('_', ' ') || 'tüm zamanlar'}
                </div>
              </div>
            )}
          </div>
        </div>
        
        <Button onClick={loadPopularProducts} variant="outline" size="sm">
          🔄 Verileri Yenile
        </Button>
      </div>
    );
  };

  const AdminDashboardEditor = ({ block }) => {
    const [sections, setSections] = useState(block?.sections || []);

    const addSection = (type) => {
      const newSection = {
        type,
        id: Date.now().toString(),
        ...(type === 'stat_grid' && {
          items: [
            { label: 'Yeni İstatistik', value: 0 }
          ]
        }),
        ...(type === 'popular_products' && {
          source: 'db',
          limit: 8,
          title: 'Popüler Ürünler'
        }),
        ...(type === 'ad_boards' && {
          items: [
            {
              title: 'Yeni Kampanya',
              subtitle: 'Açıklama',
              image: '/assets/placeholder.jpg',
              cta: { text: 'Detaylar', href: '#' }
            }
          ]
        })
      };
      setSections([...sections, newSection]);
    };

    const removeSection = (index) => {
      setSections(sections.filter((_, i) => i !== index));
    };

    const updateSection = (index, updatedSection) => {
      const newSections = [...sections];
      newSections[index] = updatedSection;
      setSections(newSections);
    };

    const moveSection = (index, direction) => {
      const newSections = [...sections];
      const targetIndex = direction === 'up' ? index - 1 : index + 1;
      
      if (targetIndex >= 0 && targetIndex < newSections.length) {
        [newSections[index], newSections[targetIndex]] = [newSections[targetIndex], newSections[index]];
        setSections(newSections);
      }
    };

    const handleSave = () => {
      const updatedBlock = {
        ...block,
        sections,
        updated_at: new Date().toISOString()
      };
      saveContentBlock(updatedBlock);
    };

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h3 className="text-xl font-bold">Admin Dashboard Düzenleyici</h3>
          <div className="space-x-2">
            <Button onClick={handleSave} disabled={loading}>
              💾 Kaydet
            </Button>
            <Button variant="outline" onClick={() => setEditMode(false)}>
              ✖️ İptal
            </Button>
          </div>
        </div>

        {/* Add Section Buttons */}
        <div className="flex gap-2 p-4 bg-gray-50 rounded-lg">
          <Button 
            size="sm" 
            variant="outline" 
            onClick={() => addSection('stat_grid')}
          >
            ➕ İstatistik Grid
          </Button>
          <Button 
            size="sm" 
            variant="outline" 
            onClick={() => addSection('popular_products')}
          >
            ➕ Popüler Ürünler
          </Button>
          <Button 
            size="sm" 
            variant="outline" 
            onClick={() => addSection('ad_boards')}
          >
            ➕ Reklam Panosu
          </Button>
        </div>

        {/* Sections List with Drag & Drop */}
        <div className="space-y-4">
          {sections.map((section, index) => (
            <Card 
              key={section.id || index} 
              className="border-2 cursor-move hover:border-orange-300 transition-colors"
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData('text/plain', index.toString());
                e.currentTarget.style.opacity = '0.5';
              }}
              onDragEnd={(e) => {
                e.currentTarget.style.opacity = '1';
              }}
              onDragOver={(e) => {
                e.preventDefault();
                e.currentTarget.style.borderColor = '#fb923c';
              }}
              onDragLeave={(e) => {
                e.currentTarget.style.borderColor = '';
              }}
              onDrop={(e) => {
                e.preventDefault();
                e.currentTarget.style.borderColor = '';
                const draggedIndex = parseInt(e.dataTransfer.getData('text/plain'));
                const targetIndex = index;
                
                if (draggedIndex !== targetIndex) {
                  const newSections = [...sections];
                  const [draggedSection] = newSections.splice(draggedIndex, 1);
                  newSections.splice(targetIndex, 0, draggedSection);
                  setSections(newSections);
                  toast.success('Bölüm sırası değiştirildi');
                }
              }}
            >
              <CardHeader className="pb-2">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600">
                      ⋮⋮
                    </div>
                    <CardTitle className="text-lg capitalize">
                      {section.type.replace('_', ' ')}
                    </CardTitle>
                    <Badge variant="outline" className="text-xs">
                      #{index + 1}
                    </Badge>
                  </div>
                  <div className="flex gap-2">
                    {index > 0 && (
                      <Button 
                        size="sm" 
                        variant="ghost"
                        onClick={() => moveSection(index, 'up')}
                        title="Yukarı taşı"
                      >
                        ⬆️
                      </Button>
                    )}
                    {index < sections.length - 1 && (
                      <Button 
                        size="sm" 
                        variant="ghost"
                        onClick={() => moveSection(index, 'down')}
                        title="Aşağı taşı"
                      >
                        ⬇️
                      </Button>
                    )}
                    <Button 
                      size="sm" 
                      variant="destructive"
                      onClick={() => {
                        if (window.confirm('Bu bölümü silmek istediğinizden emin misiniz?')) {
                          removeSection(index);
                        }
                      }}
                      title="Sil"
                    >
                      🗑️
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <SectionEditor 
                  section={section} 
                  onUpdate={(updatedSection) => updateSection(index, updatedSection)}
                />
              </CardContent>
            </Card>
          ))}
          
          {sections.length === 0 && (
            <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
              <div className="text-gray-500 mb-4">
                📋 Henüz hiç bölüm eklenmemiş
              </div>
              <div className="text-sm text-gray-400">
                Yukarıdaki butonları kullanarak bölüm ekleyebilirsin
              </div>
            </div>
          )}
        </div>

        {/* Live Preview */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>🔍 Canlı Önizleme</CardTitle>
          </CardHeader>
          <CardContent>
            <AdminDashboardPreview sections={sections} />
          </CardContent>
        </Card>
      </div>
    );
  };

  const SectionEditor = ({ section, onUpdate }) => {
    const handleChange = (field, value) => {
      onUpdate({ ...section, [field]: value });
    };

    if (section.type === 'stat_grid') {
      return (
        <div className="space-y-4">
          <Label>İstatistik Öğeleri</Label>
          {section.items?.map((item, index) => (
            <div key={index} className="flex gap-2 p-2 border rounded">
              <Input
                placeholder="Label"
                value={item.label}
                onChange={(e) => {
                  const newItems = [...section.items];
                  newItems[index] = { ...item, label: e.target.value };
                  handleChange('items', newItems);
                }}
              />
              <Input
                type="number"
                placeholder="Value"
                value={item.value}
                onChange={(e) => {
                  const newItems = [...section.items];
                  newItems[index] = { ...item, value: parseInt(e.target.value) || 0 };
                  handleChange('items', newItems);
                }}
              />
              <Button
                size="sm"
                variant="destructive"
                onClick={() => {
                  const newItems = section.items.filter((_, i) => i !== index);
                  handleChange('items', newItems);
                }}
              >
                ✖️
              </Button>
            </div>
          ))}
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              const newItems = [...(section.items || []), { label: 'Yeni İstatistik', value: 0 }];
              handleChange('items', newItems);
            }}
          >
            ➕ İstatistik Ekle
          </Button>
        </div>
      );
    }

    if (section.type === 'popular_products') {
      return (
        <PopularProductsEditor section={section} onUpdate={onUpdate} />
      );
    }

    if (section.type === 'ad_boards') {
      return (
        <div className="space-y-4">
          <Label>Reklam Panosu Öğeleri</Label>
          {section.items?.map((item, index) => (
            <div key={index} className="p-4 border rounded space-y-2">
              <Input
                placeholder="Başlık"
                value={item.title}
                onChange={(e) => {
                  const newItems = [...section.items];
                  newItems[index] = { ...item, title: e.target.value };
                  handleChange('items', newItems);
                }}
              />
              <Textarea
                placeholder="Alt başlık"
                value={item.subtitle}
                onChange={(e) => {
                  const newItems = [...section.items];
                  newItems[index] = { ...item, subtitle: e.target.value };
                  handleChange('items', newItems);
                }}
              />
              <div className="flex gap-2">
                <Input
                  placeholder="CTA Metni"
                  value={item.cta?.text || ''}
                  onChange={(e) => {
                    const newItems = [...section.items];
                    newItems[index] = { 
                      ...item, 
                      cta: { ...item.cta, text: e.target.value }
                    };
                    handleChange('items', newItems);
                  }}
                />
                <Input
                  placeholder="CTA Link"
                  value={item.cta?.href || ''}
                  onChange={(e) => {
                    const newItems = [...section.items];
                    newItems[index] = { 
                      ...item, 
                      cta: { ...item.cta, href: e.target.value }
                    };
                    handleChange('items', newItems);
                  }}
                />
              </div>
              <Button
                size="sm"
                variant="destructive"
                onClick={() => {
                  const newItems = section.items.filter((_, i) => i !== index);
                  handleChange('items', newItems);
                }}
              >
                🗑️ Sil
              </Button>
            </div>
          ))}
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              const newItems = [...(section.items || []), {
                title: 'Yeni Kampanya',
                subtitle: 'Açıklama',
                image: '/assets/placeholder.jpg',
                cta: { text: 'Detaylar', href: '#' }
              }];
              handleChange('items', newItems);
            }}
          >
            ➕ Reklam Ekle
          </Button>
        </div>
      );
    }

    return <div>Bu bölüm türü için editör henüz hazır değil</div>;
  };

  const AdminDashboardPreview = ({ sections }) => {
    const [popularProducts, setPopularProducts] = useState([]);
    
    // Load popular products for preview
    useEffect(() => {
      const loadPopularProducts = async () => {
        try {
          const response = await apiClient.get('/content/popular-products?limit=4');
          setPopularProducts(response.data || []);
        } catch (error) {
          console.error('Error loading popular products:', error);
        }
      };
      loadPopularProducts();
    }, []);
    
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sections.map((section, index) => (
          <Card key={index} className="border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                {section.type.replace('_', ' ').toUpperCase()}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {section.type === 'stat_grid' && (
                <div className="grid grid-cols-2 gap-2">
                  {section.items?.map((item, i) => (
                    <div key={i} className="text-center p-2 bg-gray-50 rounded">
                      <div className="text-lg font-bold">{item.value}</div>
                      <div className="text-xs text-gray-600">{item.label}</div>
                    </div>
                  ))}
                </div>
              )}
              {section.type === 'popular_products' && (
                <div className="space-y-2">
                  <div className="font-medium text-center mb-2">{section.title}</div>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {popularProducts.slice(0, section.limit || 8).map((product, i) => (
                      <div key={i} className="flex justify-between items-center p-2 bg-blue-50 rounded text-xs">
                        <div>
                          <div className="font-medium">{product.name}</div>
                          <div className="text-gray-600">{product.business_name || 'Restaurant'}</div>
                        </div>
                        <div className="text-blue-600 font-bold">
                          {product.order_count} sipariş
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="text-xs text-gray-500 text-center">
                    Toplam {section.limit || 8} ürün gösteriliyor
                  </div>
                </div>
              )}
              {section.type === 'ad_boards' && (
                <div className="space-y-2">
                  {section.items?.map((item, i) => (
                    <div key={i} className="p-2 bg-orange-50 rounded text-sm">
                      <div className="font-medium">{item.title}</div>
                      <div className="text-xs text-gray-600">{item.subtitle}</div>
                      <div className="text-xs mt-1">
                        <span className="bg-orange-200 px-2 py-1 rounded">
                          {item.cta?.text}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  if (loading && contentBlocks.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          <p>İçerik blokları yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">📝 İçerik Editörü</h2>
        <p className="text-gray-600">
          Website içeriklerini yönetin ve düzenleyin
        </p>
      </div>

      {!editMode ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {contentBlocks.map((block) => (
            <Card key={block._id} className="cursor-pointer hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="text-lg">{block.title}</CardTitle>
                {block.subtitle && (
                  <p className="text-sm text-gray-600">{block.subtitle}</p>
                )}
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {block._id === 'home_admin' && (
                    <div className="text-sm text-gray-600">
                      {block.sections?.length || 0} bölüm
                    </div>
                  )}
                  <div className="text-xs text-gray-500">
                    Son güncelleme: {new Date(block.updated_at).toLocaleDateString('tr-TR')}
                  </div>
                  <Button 
                    className="w-full"
                    onClick={() => {
                      setSelectedBlock(block);
                      setEditMode(true);
                    }}
                  >
                    ✏️ Düzenle
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        selectedBlock && selectedBlock._id === 'home_admin' ? (
          <AdminDashboardEditor block={selectedBlock} />
        ) : (
          <div className="text-center p-8">
            <h3 className="text-xl font-bold mb-4">
              {selectedBlock?.title} Editörü
            </h3>
            <p className="text-gray-600 mb-4">
              Bu içerik bloğu için editör henüz hazırlanmadı.
            </p>
            <Button onClick={() => setEditMode(false)}>
              ⬅️ Geri Dön
            </Button>
          </div>
        )
      )}
    </div>
  );
};

export default ContentEditor;