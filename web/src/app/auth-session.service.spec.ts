import '@angular/compiler';
import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryStorage } from '../testing/memory-storage';
import { AuthSessionService } from './auth-session.service';

vi.mock('axios', () => ({
  default: {
    post: vi.fn()
  }
}));

describe('AuthSessionService', () => {
  let storage: MemoryStorage;
  let service: AuthSessionService;

  beforeEach(() => {
    storage = new MemoryStorage();
    vi.stubGlobal('localStorage', storage);
    vi.clearAllMocks();
    service = new AuthSessionService();
  });

  it('persists a valid login session and preserves the login request contract', async () => {
    vi.mocked(axios.post).mockResolvedValue({
      data: { token: 'test-token', user: { username: 'student' } }
    } as never);

    const result = await service.login('student', 'test-password');

    expect(result.kind).toBe('authenticated');
    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:8080/auth/login',
      { username: 'student', password: 'test-password', client: 'angular-workshop' },
      { timeout: 5000 }
    );
    expect(storage.getItem('workshop_token')).toBe('test-token');
    expect(JSON.parse(storage.getItem('workshop_user') || '{}')).toEqual({ username: 'student' });
  });

  it('does not persist a response without a token', async () => {
    vi.mocked(axios.post).mockResolvedValue({
      data: { user: { username: 'student' } }
    } as never);

    const result = await service.login('student', 'test-password');

    expect(result.kind).toBe('missing-token');
    expect(storage.getItem('workshop_token')).toBeNull();
    expect(storage.getItem('workshop_user')).toBeNull();
  });

  it('does not persist a token when the response has no valid user', async () => {
    vi.mocked(axios.post).mockResolvedValue({
      data: { token: 'test-token' }
    } as never);

    const result = await service.login('student', 'test-password');

    expect(result.kind).toBe('invalid-user');
    expect(storage.getItem('workshop_token')).toBeNull();
    expect(storage.getItem('workshop_user')).toBeNull();
  });

  it('returns a stored session with a valid user', () => {
    storage.setItem('workshop_token', 'test-token');
    storage.setItem('workshop_user', JSON.stringify({ username: 'student' }));

    expect(service.getStoredSession()).toEqual({
      kind: 'authenticated',
      session: { token: 'test-token', user: { username: 'student' } }
    });
  });

  it('clears token and user when the stored user is invalid JSON', () => {
    storage.setItem('workshop_token', 'test-token');
    storage.setItem('workshop_user', 'undefined');

    expect(service.getStoredSession()).toEqual({ kind: 'invalid-user' });
    expect(storage.getItem('workshop_token')).toBeNull();
    expect(storage.getItem('workshop_user')).toBeNull();
  });

  it('clears token and user when the stored user is absent', () => {
    storage.setItem('workshop_token', 'test-token');

    expect(service.getStoredSession()).toEqual({ kind: 'invalid-user' });
    expect(storage.getItem('workshop_token')).toBeNull();
    expect(storage.getItem('workshop_user')).toBeNull();
  });

  it('rejects a parsed user without a username and clears the session', () => {
    storage.setItem('workshop_token', 'test-token');
    storage.setItem('workshop_user', JSON.stringify({ displayName: 'Student' }));

    expect(service.getStoredSession()).toEqual({ kind: 'invalid-user' });
    expect(storage.getItem('workshop_token')).toBeNull();
    expect(storage.getItem('workshop_user')).toBeNull();
  });

  it('returns missing-token when no session exists', () => {
    expect(service.getStoredSession()).toEqual({ kind: 'missing-token' });
  });

  it('removes both session values when clearing the session', () => {
    storage.setItem('workshop_token', 'test-token');
    storage.setItem('workshop_user', JSON.stringify({ username: 'student' }));

    service.clearSession();

    expect(storage.getItem('workshop_token')).toBeNull();
    expect(storage.getItem('workshop_user')).toBeNull();
  });
});
