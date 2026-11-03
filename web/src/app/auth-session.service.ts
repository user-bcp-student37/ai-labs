import { Injectable } from '@angular/core';
import axios from 'axios';

const AUTH_LOGIN_URL = 'http://localhost:8080/auth/login';
const AUTH_REQUEST_TIMEOUT_MS = 5000;
const LOGIN_CLIENT_ID = 'angular-workshop';
const TOKEN_STORAGE_KEY = 'workshop_token';
const USER_STORAGE_KEY = 'workshop_user';

export interface AuthUser {
  username: string;
  displayName?: string | null;
}

export interface AuthSession {
  token: string;
  user: AuthUser;
}

export type AuthSessionResult =
  | { kind: 'authenticated'; session: AuthSession }
  | { kind: 'missing-token' }
  | { kind: 'invalid-user' };

@Injectable({ providedIn: 'root' })
export class AuthSessionService {
  async login(username: string, password: string): Promise<AuthSessionResult> {
    const response = await axios.post<unknown>(
      AUTH_LOGIN_URL,
      { username, password, client: LOGIN_CLIENT_ID },
      { timeout: AUTH_REQUEST_TIMEOUT_MS }
    );
    const responseBody = response.data;

    if (!isRecord(responseBody) || !isNonEmptyString(responseBody['token'])) {
      return { kind: 'missing-token' };
    }

    const user = responseBody['user'];
    if (!isAuthUser(user)) {
      return { kind: 'invalid-user' };
    }

    const session = { token: responseBody['token'], user };
    localStorage.setItem(TOKEN_STORAGE_KEY, session.token);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(session.user));
    return { kind: 'authenticated', session };
  }

  getStoredSession(): AuthSessionResult {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    const serializedUser = localStorage.getItem(USER_STORAGE_KEY);

    if (serializedUser === null) {
      if (token) {
        this.clearSession();
        return { kind: 'invalid-user' };
      }
      return { kind: 'missing-token' };
    }

    let user: unknown;
    try {
      user = JSON.parse(serializedUser);
    } catch {
      this.clearSession();
      return { kind: 'invalid-user' };
    }

    if (!isAuthUser(user)) {
      this.clearSession();
      return { kind: 'invalid-user' };
    }

    if (!token) {
      return { kind: 'missing-token' };
    }

    return { kind: 'authenticated', session: { token, user } };
  }

  clearSession(): void {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function isAuthUser(value: unknown): value is AuthUser {
  if (!isRecord(value) || !isNonEmptyString(value['username'])) {
    return false;
  }

  const displayName = value['displayName'];
  return displayName === undefined || displayName === null || typeof displayName === 'string';
}
