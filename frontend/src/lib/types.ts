export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
}

export interface AuthResponse {
  user: User;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
}

export interface Alert {
  id: number;
  severity_level: string;
  region: string;
  description: string;
  timestamp: string;
  source: string;
}

export interface CreateAlertPayload {
  severity_level: string;
  region: string;
  description: string;
  source: string;
}

export interface MessageResponse {
  message: string;
}
