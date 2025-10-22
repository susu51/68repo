import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';
import { Button } from './ui/button.jsx';
import { Star } from 'lucide-react';
import { toast } from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://courier-dashboard-3.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const RatingModal = ({ order, onClose }) => {
  const [courierRating, setCourierRating] = useState(0);
  const [courierComment, setCourierComment] = useState('');
  const [businessRating, setBusinessRating] = useState(0);
  const [businessComment, setBusinessComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const StarRating = ({ rating, onRate }) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => onRate(star)}
            className="focus:outline-none transition-transform hover:scale-110"
          >
            <Star
              className={`h-8 w-8 ${
                star <= rating
                  ? 'fill-yellow-400 text-yellow-400'
                  : 'text-gray-300'
              }`}
            />
          </button>
        ))}
      </div>
    );
  };

  const handleSubmit = async () => {
    try {
      if (courierRating === 0 && businessRating === 0) {
        toast.error('Lütfen en az bir değerlendirme yapın');
        return;
      }

      setSubmitting(true);

      const ratings = [];
      
      if (courierRating > 0 && order.courier_id) {
        ratings.push({
          targetType: 'courier',
          targetId: order.courier_id,
          orderId: order._id,
          stars: courierRating,
          comment: courierComment || undefined
        });
      }

      if (businessRating > 0 && order.business_id) {
        ratings.push({
          targetType: 'business',
          targetId: order.business_id,
          orderId: order._id,
          stars: businessRating,
          comment: businessComment || undefined
        });
      }

      for (const rating of ratings) {
        const response = await fetch(`${API}/customer/ratings`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(rating)
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail);
        }
      }

      toast.success('Değerlendirmeniz kaydedildi, teşekkürler!');
      onClose();
    } catch (error) {
      console.error('Değerlendirme hatası:', error);
      toast.error(error.message || 'Değerlendirme gönderilemedi');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <CardTitle>Siparişinizi Değerlendirin</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {order.courier_id && (
            <div className="space-y-3">
              <h3 className="font-semibold text-lg">Kurye Değerlendirmesi</h3>
              <StarRating rating={courierRating} onRate={setCourierRating} />
              <textarea
                placeholder="Yorumunuz (opsiyonel)"
                value={courierComment}
                onChange={(e) => setCourierComment(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
            </div>
          )}

          <div className="space-y-3">
            <h3 className="font-semibold text-lg">İşletme Değerlendirmesi</h3>
            <StarRating rating={businessRating} onRate={setBusinessRating} />
            <textarea
              placeholder="Yorumunuz (opsiyonel)"
              value={businessComment}
              onChange={(e) => setBusinessComment(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>

          <div className="flex gap-3">
            <Button onClick={handleSubmit} disabled={submitting} className="flex-1">
              {submitting ? 'Gönderiliyor...' : 'Değerlendirmeyi Gönder'}
            </Button>
            <Button variant="outline" onClick={onClose} disabled={submitting}>
              Şimdi Değil
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};