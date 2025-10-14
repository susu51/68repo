import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card.jsx';
import { CreditCard, Wallet, Smartphone, Check } from 'lucide-react';

const paymentMethods = [
  {
    id: 'cash_on_delivery',
    title: 'Kapıda Nakit',
    description: 'Kurye geldiğinde nakit ödeme',
    icon: Wallet,
    badge: 'Popüler',
    badgeColor: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
  },
  {
    id: 'pos_on_delivery',
    title: 'Kapıda POS',
    description: 'Kurye geldiğinde kredi kartı ile ödeme',
    icon: CreditCard,
    badge: null
  },
  {
    id: 'online',
    title: 'Online Ödeme',
    description: 'Şimdi kredi kartı ile öde (Mock)',
    icon: Smartphone,
    badge: 'Güvenli',
    badgeColor: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
  }
];

export const PaymentOptionsEnhanced = ({ selectedMethod, onMethodSelect }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-primary" />
          Ödeme Yöntemi
        </CardTitle>
        <CardDescription>
          Nasıl ödeme yapmak istersiniz?
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {paymentMethods.map((method) => {
            const Icon = method.icon;
            const isSelected = selectedMethod === method.id;

            return (
              <div
                key={method.id}
                onClick={() => onMethodSelect(method.id)}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                  isSelected
                    ? 'border-primary bg-primary/5 shadow-orange'
                    : 'border-border hover:border-primary/50 hover:shadow-md'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${
                    isSelected ? 'bg-primary text-primary-foreground' : 'bg-secondary text-foreground'
                  }`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-foreground">{method.title}</h4>
                      {method.badge && (
                        <span className={`text-xs font-medium px-2 py-1 rounded-full ${method.badgeColor}`}>
                          {method.badge}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {method.description}
                    </p>
                  </div>

                  {isSelected && (
                    <div className="flex-shrink-0">
                      <div className="bg-primary text-primary-foreground rounded-full p-1">
                        <Check className="h-4 w-4" />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Info Notice */}
        {selectedMethod === 'online' && (
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-xs text-blue-700 dark:text-blue-300">
              ℹ️ <strong>Demo Mod:</strong> Online ödeme mock olarak işlenecektir. 
              Gerçek kart bilgisi gerekmez. Sipariş otomatik olarak "paid_mock" statüsüyle oluşturulacak.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
