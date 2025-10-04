import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { toast } from 'react-hot-toast';
import axios from 'axios';

const Profile = ({ user, onBack, onLogout }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-red-50 p-4">
      <div className="max-w-7xl mx-auto">
        <Card className="mb-6 border-0 shadow-xl rounded-3xl bg-gradient-to-r from-purple-500 via-pink-500 to-red-500 text-white overflow-hidden">
          <CardContent className="p-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Button
                  onClick={onBack}
                  className="bg-white/20 hover:bg-white/30 text-white rounded-full w-12 h-12 p-0 mr-4"
                >
                  ←
                </Button>
                <div>
                  <h1 className="text-3xl font-bold">👤 Profil</h1>
                  <p className="text-white/90 text-lg">Hesap ayarlarınızı yönetin</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold">{user?.first_name} {user?.last_name}</div>
                <div className="text-white/80 text-sm">{user?.email}</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-0 shadow-lg rounded-2xl">
          <CardContent className="p-6 text-center">
            <h2 className="text-xl font-bold mb-4">Profile Page</h2>
            <p>Profile functionality will be implemented here.</p>
            <Button 
              onClick={onLogout}
              className="mt-4 bg-red-500 hover:bg-red-600 text-white rounded-xl px-6 py-3"
            >
              🚪 Çıkış Yap
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Profile;