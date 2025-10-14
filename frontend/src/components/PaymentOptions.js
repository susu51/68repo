import React from 'react';
import { Card, CardContent } from './ui/card.jsx';
import { CreditCard, Banknote, Smartphone } from 'lucide-react';

export const PaymentOptions = ({ selectedMethod, onMethodSelect }) => {
  const paymentMethods = [
    { id: 'cash', label: 'Kapıda Nakit Ödeme', icon: Banknote, description: 'Kurye teslim sırasında nakit alacak' },
    { id: 'pos', label: 'Kapıda POS ile Ödeme', icon: CreditCard, description: 'Kurye ile kart okuyucu gelecek' },
    { id: 'online', label: 'Online Ödeme (Mock)', icon: Smartphone, description: 'Test amaçlı mock ödeme' }
  ];

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Ödeme Yöntemi Seçin</h2>
      
      <div className="grid gap-3">
        {paymentMethods.map((method) => {
          const Icon = method.icon;
          return (
            <Card
              key={method.id}
              className={`cursor-pointer transition-all ${
                selectedMethod === method.id
                  ? 'border-green-500 bg-green-50 ring-2 ring-green-500'
                  : 'hover:border-gray-400'
              }`}
              onClick={() => onMethodSelect(method.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-full ${
                    selectedMethod === method.id ? 'bg-green-600' : 'bg-gray-200'
                  }`}>
                    <Icon className={`h-6 w-6 ${
                      selectedMethod === method.id ? 'text-white' : 'text-gray-600'
                    }`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold">{method.label}</h3>
                    <p className="text-sm text-gray-600">{method.description}</p>
                  </div>
                  {selectedMethod === method.id && (
                    <div className="w-6 h-6 rounded-full bg-green-600 flex items-center justify-center">
                      <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};