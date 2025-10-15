import React from 'react';
import { Card, CardContent } from '../../components/ui/card';
import { ShoppingBag } from 'lucide-react';

export const OrdersManagement = () => {
  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6">
      <h1 className="text-2xl font-bold text-foreground mb-6">Siparişler</h1>
      <Card>
        <CardContent className="text-center py-12">
          <ShoppingBag className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Sipariş Yönetimi</h3>
          <p className="text-muted-foreground">Yakında aktif olacak</p>
        </CardContent>
      </Card>
    </div>
  );
};