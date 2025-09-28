import React, { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";

const API = process.env.REACT_APP_BACKEND_URL;

// Test minimal AdminDashboard
const AdminDashboard = ({ user }) => {
  const { logout } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  const [isDarkMode, setIsDarkMode] = useState(false);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between h-16">
            <h1 className="text-xl font-semibold text-red-600">Admin Panel</h1>
            <Button onClick={toggleTheme}>Toggle Theme</Button>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Card>
          <CardContent className="p-6">
            <p>Admin Dashboard Content - Tab: {activeTab}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboard;