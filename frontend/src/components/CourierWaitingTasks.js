// Courier Waiting Tasks Component - Phase 2
// Shows waiting tasks on map with accept button

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { MapPin, DollarSign, Clock, CheckCircle } from 'lucide-react';
import { toast } from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://admin-wsocket.preview.emergentagent.com';

export const CourierWaitingTasks = ({ courierId }) => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [mapCenter, setMapCenter] = useState({ lat: 38.3687, lng: 34.0254 }); // Aksaray

  useEffect(() => {
    fetchWaitingTasks();
    
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchWaitingTasks, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchWaitingTasks = async () => {
    try {
      setLoading(true);
      
      const response = await fetch(`${BACKEND_URL}/api/courier/tasks?status=waiting`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Fetched waiting tasks:', data.length);
        setTasks(data);
      } else {
        console.error('❌ Failed to fetch tasks:', response.status);
      }
    } catch (error) {
      console.error('❌ Error fetching tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const acceptTask = async (taskId) => {
    try {
      console.log('🎯 Accepting task:', taskId);
      
      const response = await fetch(`${BACKEND_URL}/api/courier/tasks/${taskId}/accept`, {
        method: 'PUT',
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Task accepted:', data);
        
        toast.success('Paket başarıyla alındı!', {
          duration: 4000,
          icon: '✅'
        });
        
        // Refresh tasks
        await fetchWaitingTasks();
        setSelectedTask(null);
      } else {
        const error = await response.json();
        console.error('❌ Accept error:', error);
        toast.error(error.detail || 'Paket kabul edilemedi');
      }
    } catch (error) {
      console.error('❌ Error accepting task:', error);
      toast.error('Bir hata oluştu');
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Bekleyen Paketler</h2>
          <p className="text-muted-foreground">Müsait paketleri görüntüleyin ve kabul edin</p>
        </div>
        <Button onClick={fetchWaitingTasks} variant="outline" size="sm" disabled={loading}>
          {loading ? '⏳' : '🔄'} Yenile
        </Button>
      </div>

      {/* Stats */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Bekleyen Paketler</p>
              <p className="text-2xl font-bold">{tasks.length}</p>
            </div>
            <div className="p-3 rounded-xl bg-orange-100 dark:bg-orange-900/20">
              <Clock className="h-6 w-6 text-orange-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tasks List */}
      {loading && tasks.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Paketler yükleniyor...</p>
          </CardContent>
        </Card>
      ) : tasks.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <Clock className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Bekleyen paket yok</h3>
            <p className="text-muted-foreground">
              Yeni paketler geldiğinde burada görünecek
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tasks.map((task) => (
            <Card key={task.id} className="card-hover-lift cursor-pointer" onClick={() => setSelectedTask(task)}>
              <CardContent className="p-4">
                <div className="space-y-3">
                  {/* Restaurant Name */}
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold">{task.restaurant_name || 'Restoran'}</h3>
                      <Badge variant="outline" className="mt-1">Bekliyor</Badge>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-600">₺{task.unit_delivery_fee.toFixed(2)}</p>
                      <p className="text-xs text-muted-foreground">Paket ücreti</p>
                    </div>
                  </div>

                  {/* Pickup Address */}
                  <div className="flex items-start gap-2 text-sm">
                    <MapPin className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-muted-foreground">Alım Noktası:</p>
                      <p className="text-foreground">{task.pickup_address || 'Adres bilgisi yok'}</p>
                    </div>
                  </div>

                  {/* Dropoff Address */}
                  <div className="flex items-start gap-2 text-sm">
                    <MapPin className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-muted-foreground">Teslimat:</p>
                      <p className="text-foreground">{task.dropoff_address || 'Adres bilgisi yok'}</p>
                    </div>
                  </div>

                  {/* Accept Button */}
                  <Button
                    data-testid="accept-task-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      acceptTask(task.id);
                    }}
                    className="w-full bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Al - Kabul Et
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Task Detail Modal */}
      {selectedTask && (
        <div 
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedTask(null)}
        >
          <Card className="max-w-2xl w-full" onClick={(e) => e.stopPropagation()}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Paket Detayları</span>
                <Button variant="ghost" size="sm" onClick={() => setSelectedTask(null)}>✕</Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Restoran</Label>
                  <p className="font-semibold">{selectedTask.restaurant_name}</p>
                </div>
                <div>
                  <Label>Paket Ücreti</Label>
                  <p className="font-semibold text-green-600">₺{selectedTask.unit_delivery_fee.toFixed(2)}</p>
                </div>
              </div>

              <div>
                <Label>Alım Noktası</Label>
                <p className="text-sm">{selectedTask.pickup_address}</p>
                <p className="text-xs text-muted-foreground">
                  Konum: {selectedTask.pickup_coords?.lat?.toFixed(6)}, {selectedTask.pickup_coords?.lng?.toFixed(6)}
                </p>
              </div>

              <div>
                <Label>Teslimat Adresi</Label>
                <p className="text-sm">{selectedTask.dropoff_address}</p>
                <p className="text-xs text-muted-foreground">
                  Konum: {selectedTask.dropoff_coords?.lat?.toFixed(6)}, {selectedTask.dropoff_coords?.lng?.toFixed(6)}
                </p>
              </div>

              <Button
                onClick={() => acceptTask(selectedTask.id)}
                className="w-full bg-green-600 hover:bg-green-700"
                size="lg"
              >
                <CheckCircle className="h-5 w-5 mr-2" />
                Paketi Kabul Et
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default CourierWaitingTasks;
