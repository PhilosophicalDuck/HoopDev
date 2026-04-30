import { api } from './client'

export interface RegisterData { username: string; email: string; password: string }
export interface LoginData { email: string; password: string }
export interface TokenResponse { access_token: string; token_type: string; user: UserData }
export interface UserData { id: number; username: string; email: string; created_at: string }

export const register = (data: RegisterData) =>
  api.post<TokenResponse>('/auth/register', data).then(r => r.data)

export const login = (data: LoginData) =>
  api.post<TokenResponse>('/auth/login', data).then(r => r.data)

export const demoLogin = () =>
  api.post<TokenResponse>('/auth/demo').then(r => r.data)
