import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'react-hot-toast';
import { apiClient } from '../utils/apiClient';

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

        {/* Sections List */}
        <div className="space-y-4">
          {sections.map((section, index) => (
            <Card key={section.id || index} className="border-2">
              <CardHeader className="pb-2">
                <div className="flex justify-between items-center">
                  <CardTitle className="text-lg capitalize">
                    {section.type.replace('_', ' ')}
                  </CardTitle>
                  <div className="flex gap-2">
                    {index > 0 && (
                      <Button 
                        size="sm" 
                        variant="ghost"
                        onClick={() => moveSection(index, 'up')}
                      >
                        ⬆️
                      </Button>
                    )}
                    {index < sections.length - 1 && (
                      <Button 
                        size="sm" 
                        variant="ghost"
                        onClick={() => moveSection(index, 'down')}
                      >
                        ⬇️
                      </Button>
                    )}
                    <Button 
                      size="sm" 
                      variant="destructive"
                      onClick={() => removeSection(index)}
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
        <div className="space-y-4">
          <div>
            <Label>Başlık</Label>
            <Input
              value={section.title || ''}
              onChange={(e) => handleChange('title', e.target.value)}
              placeholder="Popüler Ürünler"
            />
          </div>
          <div>
            <Label>Limit</Label>
            <Input
              type="number"
              value={section.limit || 8}
              onChange={(e) => handleChange('limit', parseInt(e.target.value) || 8)}
            />
          </div>
        </div>
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
                <div className="text-center p-4 bg-blue-50 rounded">
                  <div className="font-medium">{section.title}</div>
                  <div className="text-sm text-gray-600">Limit: {section.limit}</div>
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