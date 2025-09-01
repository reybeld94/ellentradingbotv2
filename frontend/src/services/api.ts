// frontend/src/services/api.ts

const API_BASE_URL = '/api/v1';

// Función para obtener el token del localStorage
const getAuthToken = (): string | null => {
  return localStorage.getItem('token');
};

// Función para hacer requests autenticados
const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
  const token = getAuthToken();

  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Si el token es inválido, redirigir al login
  if (response.status === 401) {
    localStorage.removeItem('token');
    window.location.reload();
  }

  return response;
};

// API functions
export const api = {
  // Auth endpoints
  auth: {
    login: async (email: string, password: string) => {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      return response;
    },

    register: async (email: string, username: string, password: string, fullName?: string) => {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          username,
          password,
          full_name: fullName,
        }),
      });
      return response;
    },

    getProfile: async () => {
      return authenticatedFetch(`${API_BASE_URL}/auth/me`);
    },

    refreshToken: async () => {
      return authenticatedFetch(`${API_BASE_URL}/auth/refresh-token`, {
        method: 'POST',
      });
    },
  },

  // Trading endpoints
  trading: {
    getAccount: async () => {
      return authenticatedFetch(`${API_BASE_URL}/account`);
    },

    getSignals: async () => {
      return authenticatedFetch(`${API_BASE_URL}/signals`);
    },

    getOrders: async () => {
      return authenticatedFetch(`${API_BASE_URL}/orders`);
    },

    getTrades: async () => {
      return authenticatedFetch(`${API_BASE_URL}/trades`);
    },

    getEquityCurve: async (strategyId?: string) => {
      const query = strategyId ? `?strategy_id=${strategyId}` : '';
      return authenticatedFetch(`${API_BASE_URL}/trades/equity-curve${query}`);
    },

    getPositions: async () => {
      return authenticatedFetch(`${API_BASE_URL}/positions`);
    },

    sendWebhook: async (webhookData: any) => {
      return authenticatedFetch(`${API_BASE_URL}/webhook`, {
        method: 'POST',
        body: JSON.stringify(webhookData),
      });
    },
  },

  // Risk endpoints
  risk: {
    getStatus: async () => {
      return authenticatedFetch(`${API_BASE_URL}/risk/status`);
    },
    getAllocationChart: async () => {
      return authenticatedFetch(`${API_BASE_URL}/risk/allocation-chart`);
    },
  },

  // Portfolio endpoints
  portfolios: {
    list: async () => {
      return authenticatedFetch(`${API_BASE_URL}/portfolios`);
    },
    create: async (data: any) => {
      return authenticatedFetch(`${API_BASE_URL}/portfolios`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    update: async (id: number, data: any) => {
      return authenticatedFetch(`${API_BASE_URL}/portfolios/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    },
    delete: async (id: number) => {
      return authenticatedFetch(`${API_BASE_URL}/portfolios/${id}`, {
        method: 'DELETE',
      });
    },
    activate: async (id: number) => {
      return authenticatedFetch(`${API_BASE_URL}/portfolios/${id}/activate`, {
        method: 'POST',
      });
    },
    deactivate: async (id: number) => {
      return authenticatedFetch(`${API_BASE_URL}/portfolios/${id}/deactivate`, {
        method: 'POST',
      });
    },
  },

  // Analytics endpoints
  analytics: {
    getPerformanceMetrics: async (timeframe: string = '1M', portfolioId?: number) => {
      const params = new URLSearchParams({ timeframe });
      if (portfolioId) params.append('portfolio_id', portfolioId.toString());
      return authenticatedFetch(`${API_BASE_URL}/analytics/performance?${params}`);
    },

    getSummary: async () => {
      return authenticatedFetch(`${API_BASE_URL}/analytics/summary`);
    },

    getTradeAnalytics: async (timeframe: string = '3M', portfolioId?: number) => {
      const params = new URLSearchParams({ timeframe });
      if (portfolioId) params.append('portfolio_id', portfolioId.toString());
      return authenticatedFetch(`${API_BASE_URL}/analytics/trade-analytics?${params}`);
    },

    getEquityCurve: async (timeframe: string = '3M', portfolioId?: number) => {
      const params = new URLSearchParams({ timeframe });
      if (portfolioId) params.append('portfolio_id', portfolioId.toString());
      return authenticatedFetch(`${API_BASE_URL}/analytics/equity-curve?${params}`);
    },

    getMonthlyPerformance: async (portfolioId?: number) => {
      const params = portfolioId ? `?portfolio_id=${portfolioId}` : '';
      return authenticatedFetch(`${API_BASE_URL}/analytics/monthly-performance${params}`);
    },
  },

  // Strategy endpoints
  strategies: {
    list: async () => {
      return authenticatedFetch(`${API_BASE_URL}/strategies`);
    },

    create: async (data: any) => {
      return authenticatedFetch(`${API_BASE_URL}/strategies`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    update: async (id: number, data: any) => {
      return authenticatedFetch(`${API_BASE_URL}/strategies/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    },

    delete: async (id: number) => {
      return authenticatedFetch(`${API_BASE_URL}/strategies/${id}`, {
        method: 'DELETE',
      });
    },

    metrics: async (id: number) => {
      return authenticatedFetch(`${API_BASE_URL}/strategies/${id}/metrics`);
    },
  },

  // Admin endpoints (if user is admin)
  admin: {
    getAllSignals: async () => {
      return authenticatedFetch(`${API_BASE_URL}/admin/all-signals`);
    },

    getUserStats: async () => {
      return authenticatedFetch(`${API_BASE_URL}/admin/user-stats`);
    },
  },
};

export default api;