import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Calendar, Clock, Save } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

const WEEKDAYS = [
  { id: 0, name: 'Pazartesi', short: 'Pzt' },
  { id: 1, name: 'Salı', short: 'Sal' },
  { id: 2, name: 'Çarşamba', short: 'Çar' },
  { id: 3, name: 'Perşembe', short: 'Per' },
  { id: 4, name: 'Cuma', short: 'Cum' },
  { id: 5, name: 'Cumartesi', short: 'Cmt' },
  { id: 6, name: 'Pazar', short: 'Paz' }
];

export const CourierAvailability = () => {
  const [availability, setAvailability] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchAvailability();
  }, []);

  const fetchAvailability = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API}/courier/availability`, {
        method: 'GET',
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.availability) {
          setAvailability(data.availability);
        }
      }
    } catch (error) {
      console.error('Müsaitlik yükleme hatası:', error);
    } finally {
      setLoading(false);
    }
  };

  const isSlotActive = (weekday) => {
    return availability.some(slot => slot.weekday === weekday);
  };

  const getSlotTime = (weekday) => {
    const slot = availability.find(s => s.weekday === weekday);
    return slot ? { start: slot.start, end: slot.end } : { start: '09:00', end: '18:00' };
  };

  const toggleDay = (weekday) => {
    if (isSlotActive(weekday)) {
      // Remove the slot
      setAvailability(prev => prev.filter(slot => slot.weekday !== weekday));
    } else {
      // Add new slot with default times
      setAvailability(prev => [
        ...prev,
        { weekday, start: '09:00', end: '18:00' }
      ]);
    }
  };

  const updateSlotTime = (weekday, field, value) => {
    setAvailability(prev => prev.map(slot => 
      slot.weekday === weekday 
        ? { ...slot, [field]: value }
        : slot
    ));
  };

  const saveAvailability = async () => {
    try {
      setSaving(true);

      const response = await fetch(`${API}/courier/availability`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ slots: availability })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Müsaitlik kaydedilemedi');
      }

      const data = await response.json();
      
      if (data.success) {
        toast.success('Müsaitlik durumu başarıyla kaydedildi!');
      }
    } catch (error) {
      console.error('Müsaitlik kaydetme hatası:', error);
      toast.error('Müsaitlik kaydedilemedi: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  // Quick actions
  const selectAllWeekdays = () => {
    const weekdaySlots = [0, 1, 2, 3, 4].map(day => ({
      weekday: day,
      start: '09:00',
      end: '18:00'
    }));
    setAvailability(weekdaySlots);
  };

  const selectWeekend = () => {
    const weekendSlots = [5, 6].map(day => ({
      weekday: day,
      start: '10:00',
      end: '20:00'
    }));
    setAvailability([...availability.filter(s => s.weekday < 5), ...weekendSlots]);
  };

  const selectAllDays = () => {
    const allDaySlots = WEEKDAYS.map(day => ({
      weekday: day.id,
      start: '09:00',
      end: '22:00'
    }));
    setAvailability(allDaySlots);
  };

  const clearAll = () => {
    setAvailability([]);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Çalışma Günleri & Müsaitlik
        </CardTitle>
        <CardDescription>
          Hangi günlerde ve saatlerde çalışacağınızı belirleyin
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Quick Actions */}
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={selectAllWeekdays}>
            Hafta İçi (Pzt-Cum)
          </Button>
          <Button variant="outline" size="sm" onClick={selectWeekend}>
            Hafta Sonu
          </Button>
          <Button variant="outline" size="sm" onClick={selectAllDays}>
            Tüm Günler
          </Button>
          <Button variant="outline" size="sm" onClick={clearAll}>
            Temizle
          </Button>
        </div>

        {/* Days Selection */}
        <div className="space-y-3">
          {WEEKDAYS.map(day => {
            const isActive = isSlotActive(day.id);
            const times = getSlotTime(day.id);

            return (
              <div
                key={day.id}
                className={`border rounded-lg p-4 transition-all ${
                  isActive ? 'border-green-500 bg-green-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Button
                      variant={isActive ? "default" : "outline"}
                      size="sm"
                      onClick={() => toggleDay(day.id)}
                      className={isActive ? "bg-green-600 hover:bg-green-700" : ""}
                    >
                      {day.short}
                    </Button>
                    <Label className="font-medium">{day.name}</Label>
                  </div>

                  <div className={`flex items-center gap-2 ${!isActive ? 'invisible' : ''}`}>
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <input
                      type="time"
                      value={times.start}
                      onChange={(e) => updateSlotTime(day.id, 'start', e.target.value)}
                      disabled={!isActive}
                      className="border rounded px-2 py-1 text-sm"
                    />
                    <span className="text-muted-foreground">-</span>
                    <input
                      type="time"
                      value={times.end}
                      onChange={(e) => updateSlotTime(day.id, 'end', e.target.value)}
                      disabled={!isActive}
                      className="border rounded px-2 py-1 text-sm"
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Summary */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2">Özet</h4>
          <p className="text-sm text-blue-700">
            {availability.length === 0 ? (
              "Henüz müsait gün seçmediniz"
            ) : (
              `${availability.length} gün için müsaitlik ayarlandı`
            )}
          </p>
        </div>

        {/* Save Button */}
        <Button
          className="w-full"
          onClick={saveAvailability}
          disabled={saving || availability.length === 0}
        >
          {saving ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Kaydediliyor...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Müsaitlik Durumunu Kaydet
            </>
          )}
        </Button>

        <p className="text-xs text-muted-foreground text-center">
          Kaydettiğiniz müsaitlik durumu tekrar giriş yaptığınızda yüklenecektir
        </p>
      </CardContent>
    </Card>
  );
};
