// frontend/src/pages/Profile.tsx

import React, { useState } from "react";
import type { ReactNode } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  User,
  Mail,
  Shield,
  CheckCircle,
  XCircle,
  Edit2,
  Save,
  X,
  Key,
  Download,
  Upload,
  Settings,
  Eye,
  EyeOff,
  AlertTriangle,
  Camera,
  Briefcase,
  Award,
  Clock,
  Activity,
} from "lucide-react";

const Profile: React.FC = () => {
  const { user, token, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<
    "profile" | "security" | "preferences" | "activity"
  >("profile");
  const [isEditing, setIsEditing] = useState(false);
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [editForm, setEditForm] = useState({
    full_name: user?.full_name || "",
    email: user?.email || "",
  });
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [portfolios, setPortfolios] = useState<
    Array<{ id: number; name: string; is_active: boolean }>
  >([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<number | null>(
    null,
  );
  const [showPortfolioForm, setShowPortfolioForm] = useState(false);
  const [newPortfolio, setNewPortfolio] = useState({
    name: "",
    api_key: "",
    secret_key: "",
    base_url: "",
  });
  const [positionLimit, setPositionLimit] = useState<number>(user?.position_limit ?? 7);

  const API_BASE_URL = "/api/v1";

  React.useEffect(() => {
    const fetchPortfolios = async () => {
      if (!token) return;
      const res = await fetch(`${API_BASE_URL}/portfolios`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setPortfolios(data);
        const active = data.find((p: any) => p.is_active);
        if (active) setSelectedPortfolio(active.id);
      }
    };
    fetchPortfolios();
  }, [token]);

  const changePortfolio = async (id: number) => {
    setSelectedPortfolio(id);
    await fetch(`${API_BASE_URL}/portfolios/${id}/activate`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
  };

  const createPortfolio = async () => {
    const res = await fetch(`${API_BASE_URL}/portfolios`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(newPortfolio),
    });
    if (res.ok) {
      const data = await res.json();
      await changePortfolio(data.id);
      setPortfolios((prev) => [
        ...prev.map((p) => ({ ...p, is_active: false })),
        { id: data.id, name: data.name, is_active: true },
      ]);
      setShowPortfolioForm(false);
      setNewPortfolio({ name: "", api_key: "", secret_key: "", base_url: "" });
    }
  };

  const savePositionLimit = async () => {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ position_limit: positionLimit }),
    });
    if (res.ok) {
      const data = await res.json();
      setPositionLimit(data.position_limit);
    }
  };

  const handleSave = async () => {
    try {
      // TODO: Implementar actualización de perfil
      console.log("Saving profile:", editForm);
      setIsEditing(false);
    } catch (error) {
      console.error("Error updating profile:", error);
    }
  };

  const handleCancel = () => {
    setEditForm({
      full_name: user?.full_name || "",
      email: user?.email || "",
    });
    setIsEditing(false);
  };

  const handlePasswordChange = async () => {
    try {
      // TODO: Implementar cambio de contraseña
      console.log("Changing password");
      setShowPasswordChange(false);
      setPasswordForm({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
    } catch (error) {
      console.error("Error changing password:", error);
    }
  };

  if (!user) return null;

  const TabButton: React.FC<{
    active: boolean;
    onClick: () => void;
    icon: React.ComponentType<any>;
    children: ReactNode;
  }> = ({ active, onClick, icon: Icon, children }) => (
    <button
      onClick={onClick}
      className={`flex items-center px-6 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
        active
          ? "bg-blue-100 text-blue-700 shadow-sm"
          : "text-gray-600 hover:bg-gray-100"
      }`}
    >
      <Icon className="h-5 w-5 mr-2" />
      {children}
    </button>
  );

  const InfoCard: React.FC<{
    title: string;
    children: ReactNode;
    action?: ReactNode;
  }> = ({ title, children, action }) => (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {action}
      </div>
      {children}
    </div>
  );

  const StatCard: React.FC<{
    title: string;
    value: string;
    icon: React.ComponentType<any>;
    color: string;
  }> = ({ title, value, icon: Icon, color }) => (
    <div className={`${color} rounded-xl p-4`}>
      <div className="flex items-center">
        <Icon className="h-6 w-6 text-white mr-3" />
        <div>
          <p className="text-white/80 text-sm">{title}</p>
          <p className="text-white text-lg font-bold">{value}</p>
        </div>
      </div>
    </div>
  );

  const renderProfileTab = () => (
    <div className="space-y-6">
      {/* Profile Header */}
      <InfoCard
        title="Personal Information"
        action={
          !isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-xl transition-all duration-200"
            >
              <Edit2 className="h-4 w-4 mr-2" />
              Edit
            </button>
          ) : (
            <div className="flex space-x-2">
              <button
                onClick={handleSave}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all duration-200"
              >
                <Save className="h-4 w-4 mr-2" />
                Save
              </button>
              <button
                onClick={handleCancel}
                className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-all duration-200"
              >
                <X className="h-4 w-4 mr-2" />
                Cancel
              </button>
            </div>
          )
        }
      >
        {/* Avatar Section */}
        <div className="flex items-center mb-8">
          <div className="relative">
            <div className="w-24 h-24 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold">
              {user.username.slice(0, 2).toUpperCase()}
            </div>
            <button className="absolute bottom-0 right-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white hover:bg-blue-700 transition-colors duration-200">
              <Camera className="h-4 w-4" />
            </button>
          </div>
          <div className="ml-6">
            <h2 className="text-2xl font-bold text-gray-900">
              {user.username}
            </h2>
            <p className="text-gray-600">Professional Trader</p>
            <div className="flex items-center mt-2">
              <div className="w-2 h-2 bg-emerald-500 rounded-full mr-2"></div>
              <span className="text-sm text-emerald-600 font-medium">
                Active Account
              </span>
            </div>
          </div>
        </div>

        {/* Form Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Full Name
            </label>
            {isEditing ? (
              <input
                type="text"
                value={editForm.full_name}
                onChange={(e) =>
                  setEditForm({ ...editForm, full_name: e.target.value })
                }
                className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200"
                placeholder="Enter your full name"
              />
            ) : (
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-gray-900">{user.full_name || "Not set"}</p>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Email Address
            </label>
            {isEditing ? (
              <input
                type="email"
                value={editForm.email}
                onChange={(e) =>
                  setEditForm({ ...editForm, email: e.target.value })
                }
                className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200"
              />
            ) : (
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-gray-900">{user.email}</p>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Username
            </label>
            <div className="p-4 bg-gray-50 rounded-xl">
              <p className="text-gray-900">{user.username}</p>
              <p className="text-xs text-gray-500 mt-1">
                Username cannot be changed
              </p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Member Since
            </label>
            <div className="p-4 bg-gray-50 rounded-xl">
              <p className="text-gray-900">
                {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      </InfoCard>

      {/* Account Status */}
      <InfoCard title="Account Status">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard
            title="Account Status"
            value={user.is_active ? "Active" : "Inactive"}
            icon={user.is_active ? CheckCircle : XCircle}
            color={
              user.is_active
                ? "bg-gradient-to-r from-emerald-500 to-green-500"
                : "bg-gradient-to-r from-red-500 to-pink-500"
            }
          />
          <StatCard
            title="Email Status"
            value={user.is_verified ? "Verified" : "Unverified"}
            icon={user.is_verified ? Mail : AlertTriangle}
            color={
              user.is_verified
                ? "bg-gradient-to-r from-blue-500 to-indigo-500"
                : "bg-gradient-to-r from-yellow-500 to-orange-500"
            }
          />
          <StatCard
            title="Account Type"
            value={user.is_admin ? "Administrator" : "Professional"}
            icon={user.is_admin ? Shield : Briefcase}
            color="bg-gradient-to-r from-purple-500 to-pink-500"
          />
        </div>
      </InfoCard>

      {/* Trading Stats */}
      <InfoCard title="Trading Statistics">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-xl border border-blue-100">
            <Activity className="h-8 w-8 text-blue-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-blue-900">127</p>
            <p className="text-sm text-blue-600">Total Signals</p>
          </div>
          <div className="text-center p-4 bg-emerald-50 rounded-xl border border-emerald-100">
            <CheckCircle className="h-8 w-8 text-emerald-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-emerald-900">89</p>
            <p className="text-sm text-emerald-600">Successful Trades</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-xl border border-purple-100">
            <Award className="h-8 w-8 text-purple-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-purple-900">70.1%</p>
            <p className="text-sm text-purple-600">Success Rate</p>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-xl border border-orange-100">
            <Clock className="h-8 w-8 text-orange-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-orange-900">2.3 min</p>
            <p className="text-sm text-orange-600">Avg Fill Time</p>
          </div>
        </div>
      </InfoCard>
    </div>
  );

  const renderSecurityTab = () => (
    <div className="space-y-6">
      {/* Password Section */}
      <InfoCard
        title="Password & Security"
        action={
          <button
            onClick={() => setShowPasswordChange(!showPasswordChange)}
            className="flex items-center px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-xl transition-all duration-200"
          >
            <Key className="h-4 w-4 mr-2" />
            {showPasswordChange ? "Cancel" : "Change Password"}
          </button>
        }
      >
        {!showPasswordChange ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
              <div className="flex items-center">
                <Key className="h-5 w-5 text-gray-400 mr-3" />
                <div>
                  <p className="font-medium text-gray-900">Password</p>
                  <p className="text-sm text-gray-500">
                    Last changed 30 days ago
                  </p>
                </div>
              </div>
              <span className="text-emerald-600 text-sm font-medium">
                Strong
              </span>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Current Password
              </label>
              <div className="relative">
                <input
                  type={showPasswords.current ? "text" : "password"}
                  value={passwordForm.current_password}
                  onChange={(e) =>
                    setPasswordForm({
                      ...passwordForm,
                      current_password: e.target.value,
                    })
                  }
                  className="w-full p-4 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="Enter current password"
                />
                <button
                  type="button"
                  onClick={() =>
                    setShowPasswords({
                      ...showPasswords,
                      current: !showPasswords.current,
                    })
                  }
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPasswords.current ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                New Password
              </label>
              <div className="relative">
                <input
                  type={showPasswords.new ? "text" : "password"}
                  value={passwordForm.new_password}
                  onChange={(e) =>
                    setPasswordForm({
                      ...passwordForm,
                      new_password: e.target.value,
                    })
                  }
                  className="w-full p-4 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="Enter new password"
                />
                <button
                  type="button"
                  onClick={() =>
                    setShowPasswords({
                      ...showPasswords,
                      new: !showPasswords.new,
                    })
                  }
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPasswords.new ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Confirm New Password
              </label>
              <div className="relative">
                <input
                  type={showPasswords.confirm ? "text" : "password"}
                  value={passwordForm.confirm_password}
                  onChange={(e) =>
                    setPasswordForm({
                      ...passwordForm,
                      confirm_password: e.target.value,
                    })
                  }
                  className="w-full p-4 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="Confirm new password"
                />
                <button
                  type="button"
                  onClick={() =>
                    setShowPasswords({
                      ...showPasswords,
                      confirm: !showPasswords.confirm,
                    })
                  }
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPasswords.confirm ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            <button
              onClick={handlePasswordChange}
              className="w-full bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-all duration-200 font-medium"
            >
              Update Password
            </button>
          </div>
        )}
      </InfoCard>

      {/* Two-Factor Authentication */}
      <InfoCard title="Two-Factor Authentication">
        <div className="flex items-center justify-between p-4 bg-yellow-50 rounded-xl border border-yellow-200">
          <div className="flex items-center">
            <Shield className="h-5 w-5 text-yellow-600 mr-3" />
            <div>
              <p className="font-medium text-yellow-800">
                Two-Factor Authentication
              </p>
              <p className="text-sm text-yellow-600">
                Add an extra layer of security to your account
              </p>
            </div>
          </div>
          <button className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors duration-200 text-sm font-medium">
            Enable 2FA
          </button>
        </div>
      </InfoCard>

      {/* Login Sessions */}
      <InfoCard title="Active Sessions">
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-emerald-500 rounded-full mr-3"></div>
              <div>
                <p className="font-medium text-gray-900">Current Session</p>
                <p className="text-sm text-gray-500">
                  Chrome on Windows • Miami, FL
                </p>
              </div>
            </div>
            <span className="text-sm text-emerald-600 font-medium">
              Active now
            </span>
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-gray-400 rounded-full mr-3"></div>
              <div>
                <p className="font-medium text-gray-900">Mobile App</p>
                <p className="text-sm text-gray-500">iPhone • 2 hours ago</p>
              </div>
            </div>
            <button className="text-sm text-red-600 hover:text-red-700 font-medium">
              Revoke
            </button>
          </div>
        </div>
      </InfoCard>
    </div>
  );

  const renderPreferencesTab = () => (
    <div className="space-y-6">
      <InfoCard title="Position Limit">
        <div className="flex items-center space-x-2">
          <input
            type="number"
            value={positionLimit}
            onChange={(e) => setPositionLimit(Number(e.target.value))}
            className="w-24 p-2 border border-gray-300 rounded"
          />
          <button
            onClick={savePositionLimit}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg"
          >
            Save
          </button>
        </div>
      </InfoCard>
      <InfoCard
        title="Trading Portfolio"
        action={
          <button
            onClick={() => setShowPortfolioForm(!showPortfolioForm)}
            className="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg"
          >
            {showPortfolioForm ? "Cancel" : "Add"}
          </button>
        }
      >
        <select
          value={selectedPortfolio ?? ""}
          onChange={(e) => changePortfolio(Number(e.target.value))}
          className="w-full p-3 border border-gray-300 rounded-lg mb-4"
        >
          {portfolios.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        {showPortfolioForm && (
          <div className="space-y-2">
            <input
              type="text"
              placeholder="Name"
              value={newPortfolio.name}
              onChange={(e) =>
                setNewPortfolio({ ...newPortfolio, name: e.target.value })
              }
              className="w-full p-2 border border-gray-300 rounded"
            />
            <input
              type="text"
              placeholder="API Key"
              value={newPortfolio.api_key}
              onChange={(e) =>
                setNewPortfolio({ ...newPortfolio, api_key: e.target.value })
              }
              className="w-full p-2 border border-gray-300 rounded"
            />
            <input
              type="text"
              placeholder="Secret Key"
              value={newPortfolio.secret_key}
              onChange={(e) =>
                setNewPortfolio({ ...newPortfolio, secret_key: e.target.value })
              }
              className="w-full p-2 border border-gray-300 rounded"
            />
            <input
              type="text"
              placeholder="Base URL"
              value={newPortfolio.base_url}
              onChange={(e) =>
                setNewPortfolio({ ...newPortfolio, base_url: e.target.value })
              }
              className="w-full p-2 border border-gray-300 rounded"
            />
            <button
              onClick={createPortfolio}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg"
            >
              Save
            </button>
          </div>
        )}
      </InfoCard>
      {/* Notifications */}
      <InfoCard title="Notification Preferences">
        <div className="space-y-4">
          {[
            {
              title: "Email Notifications",
              description: "Receive email alerts for important events",
              enabled: true,
            },
            {
              title: "Signal Alerts",
              description: "Get notified when new trading signals arrive",
              enabled: true,
            },
            {
              title: "Order Confirmations",
              description: "Receive confirmations for executed orders",
              enabled: true,
            },
            {
              title: "Weekly Reports",
              description: "Get weekly performance summaries",
              enabled: false,
            },
            {
              title: "Marketing Emails",
              description: "Receive updates about new features",
              enabled: false,
            },
          ].map((pref, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-xl"
            >
              <div>
                <p className="font-medium text-gray-900">{pref.title}</p>
                <p className="text-sm text-gray-500">{pref.description}</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  defaultChecked={pref.enabled}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          ))}
        </div>
      </InfoCard>

      {/* Data Export */}
      <InfoCard title="Data & Privacy">
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center">
              <Download className="h-5 w-5 text-gray-500 mr-3" />
              <div>
                <p className="font-medium text-gray-900">Export Data</p>
                <p className="text-sm text-gray-500">
                  Download your trading data and history
                </p>
              </div>
            </div>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 text-sm font-medium">
              Download
            </button>
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center">
              <Upload className="h-5 w-5 text-gray-500 mr-3" />
              <div>
                <p className="font-medium text-gray-900">Import Data</p>
                <p className="text-sm text-gray-500">
                  Import trading data from other platforms
                </p>
              </div>
            </div>
            <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200 text-sm font-medium">
              Import
            </button>
          </div>
        </div>
      </InfoCard>
    </div>
  );

  const renderActivityTab = () => (
    <div className="space-y-6">
      {/* Recent Activity */}
      <InfoCard title="Recent Activity">
        <div className="space-y-4">
          {[
            {
              action: "Login",
              description: "Signed in from Chrome on Windows",
              time: "2 minutes ago",
              type: "login",
            },
            {
              action: "Signal Processed",
              description: "AAPL buy signal executed successfully",
              time: "1 hour ago",
              type: "signal",
            },
            {
              action: "Profile Updated",
              description: "Changed notification preferences",
              time: "3 hours ago",
              type: "profile",
            },
            {
              action: "Order Filled",
              description: "TSLA sell order completed",
              time: "5 hours ago",
              type: "order",
            },
            {
              action: "Password Changed",
              description: "Account password updated",
              time: "2 days ago",
              type: "security",
            },
          ].map((activity, index) => (
            <div
              key={index}
              className="flex items-center p-4 bg-gray-50 rounded-xl"
            >
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center mr-4 ${
                  activity.type === "login"
                    ? "bg-blue-100"
                    : activity.type === "signal"
                      ? "bg-emerald-100"
                      : activity.type === "profile"
                        ? "bg-purple-100"
                        : activity.type === "order"
                          ? "bg-orange-100"
                          : "bg-red-100"
                }`}
              >
                {activity.type === "login" && (
                  <User className="h-5 w-5 text-blue-600" />
                )}
                {activity.type === "signal" && (
                  <Activity className="h-5 w-5 text-emerald-600" />
                )}
                {activity.type === "profile" && (
                  <Settings className="h-5 w-5 text-purple-600" />
                )}
                {activity.type === "order" && (
                  <Briefcase className="h-5 w-5 text-orange-600" />
                )}
                {activity.type === "security" && (
                  <Shield className="h-5 w-5 text-red-600" />
                )}
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-900">{activity.action}</p>
                <p className="text-sm text-gray-500">{activity.description}</p>
              </div>
              <span className="text-sm text-gray-400">{activity.time}</span>
            </div>
          ))}
        </div>
      </InfoCard>
    </div>
  );

  return (
    <div className="p-8 bg-gray-50 min-h-screen max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Profile Settings
        </h1>
        <p className="text-gray-600">
          Manage your account settings and trading preferences
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-8">
        <div className="flex flex-wrap gap-2">
          <TabButton
            active={activeTab === "profile"}
            onClick={() => setActiveTab("profile")}
            icon={User}
          >
            Profile
          </TabButton>
          <TabButton
            active={activeTab === "security"}
            onClick={() => setActiveTab("security")}
            icon={Shield}
          >
            Security
          </TabButton>
          <TabButton
            active={activeTab === "preferences"}
            onClick={() => setActiveTab("preferences")}
            icon={Settings}
          >
            Preferences
          </TabButton>
          <TabButton
            active={activeTab === "activity"}
            onClick={() => setActiveTab("activity")}
            icon={Activity}
          >
            Activity
          </TabButton>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "profile" && renderProfileTab()}
      {activeTab === "security" && renderSecurityTab()}
      {activeTab === "preferences" && renderPreferencesTab()}
      {activeTab === "activity" && renderActivityTab()}

      {/* Danger Zone */}
      <div className="mt-8">
        <InfoCard title="Danger Zone">
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-red-50 rounded-xl border border-red-200">
              <div>
                <h4 className="font-semibold text-red-900">Sign Out</h4>
                <p className="text-sm text-red-600">
                  Sign out from your current session
                </p>
              </div>
              <button
                onClick={logout}
                className="px-6 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-all duration-200 font-medium"
              >
                Sign Out
              </button>
            </div>
            <div className="flex items-center justify-between p-4 bg-red-50 rounded-xl border border-red-200">
              <div>
                <h4 className="font-semibold text-red-900">Delete Account</h4>
                <p className="text-sm text-red-600">
                  Permanently delete your account and all data
                </p>
              </div>
              <button className="px-6 py-3 border border-red-600 text-red-600 rounded-xl hover:bg-red-600 hover:text-white transition-all duration-200 font-medium">
                Delete Account
              </button>
            </div>
          </div>
        </InfoCard>
      </div>
    </div>
  );
};

export default Profile;
