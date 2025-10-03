import React, { useState } from 'react';
import AddressesPage from './AddressesPage';
import NearbyRestaurants from './NearbyRestaurants';

export const CustomerMain = ({ user }) => {
  const [currentView, setCurrentView] = useState('menu'); // 'menu' | 'addresses' | 'restaurants'
  const [selectedAddress, setSelectedAddress] = useState(null);

  const handleAddressSelect = (address) => {
    console.log('Selected address:', address);
    setSelectedAddress(address);
    setCurrentView('restaurants');
  };

  const handleBackToAddresses = () => {
    setCurrentView('addresses');
    setSelectedAddress(null);
  };

  const handleRestaurantSelect = (restaurant) => {
    console.log('Selected restaurant:', restaurant);
    // Here you could navigate to restaurant detail page
    // or open menu/cart functionality
  };

  if (currentView === 'restaurants') {
    return (
      <NearbyRestaurants
        address={selectedAddress}
        city={selectedAddress?.city || selectedAddress?.city_normalized}
        lat={selectedAddress?.lat}
        lng={selectedAddress?.lng}
        onBack={handleBackToAddresses}
        onRestaurantSelect={handleRestaurantSelect}
      />
    );
  }

  return (
    <AddressesPage
      key="addresses-page"
      onSelectAddress={handleAddressSelect}
      onBack={null} // No back button on main page
    />
  );
};

export default CustomerMain;