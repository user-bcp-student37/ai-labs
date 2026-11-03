import '@angular/compiler';
import { Router } from '@angular/router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthSessionService } from '../auth-session.service';
import { LoginComponent } from './login.component';
import { MemoryStorage } from '../../testing/memory-storage';

describe('LoginComponent', () => {
  let storage: MemoryStorage;
  let navigate: ReturnType<typeof vi.fn>;
  let login: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    storage = new MemoryStorage();
    vi.stubGlobal('localStorage', storage);
    vi.clearAllMocks();
    navigate = vi.fn().mockResolvedValue(true);
    login = vi.fn();
  });

  it('persists a valid login response and navigates to the dashboard', async () => {
    login.mockResolvedValue({
      kind: 'authenticated',
      session: { token: 'test-token', user: { username: 'student' } }
    });
    const component = new LoginComponent(
      { navigate } as unknown as Router,
      { login } as unknown as AuthSessionService
    );
    component.username = 'student';
    component.password = 'test-password';

    await component.login();

    expect(login).toHaveBeenCalledWith('student', 'test-password');
    expect(storage.getItem('workshop_preferences')).toBe(JSON.stringify(component.preferences));
    expect(navigate).toHaveBeenCalledWith(['/dashboard']);
  });

  it('does not establish a session when the response has no user', async () => {
    login.mockResolvedValue({ kind: 'invalid-user' });
    const component = new LoginComponent(
      { navigate } as unknown as Router,
      { login } as unknown as AuthSessionService
    );
    component.username = 'student';
    component.password = 'test-password';

    await component.login();

    expect(storage.getItem('workshop_token')).toBeNull();
    expect(storage.getItem('workshop_user')).toBeNull();
    expect(navigate).not.toHaveBeenCalled();
    expect(component.message).not.toBe('');
  });

  it('keeps the existing missing-token message', async () => {
    login.mockResolvedValue({ kind: 'missing-token' });
    const component = new LoginComponent(
      { navigate } as unknown as Router,
      { login } as unknown as AuthSessionService
    );
    component.username = 'student';
    component.password = 'test-password';

    await component.login();

    expect(component.message).toContain('sin token');
    expect(navigate).not.toHaveBeenCalled();
  });

  it('rejects a blank username before calling the session service', async () => {
    const component = new LoginComponent(
      { navigate } as unknown as Router,
      { login } as unknown as AuthSessionService
    );
    component.password = 'test-password';

    await component.login();

    expect(component.message).toContain('Ingrese un usuario');
    expect(login).not.toHaveBeenCalled();
  });

  it('rejects a blank password before calling the session service', async () => {
    const component = new LoginComponent(
      { navigate } as unknown as Router,
      { login } as unknown as AuthSessionService
    );
    component.username = 'student';

    await component.login();

    expect(component.message).toContain('Ingrese una contraseña');
    expect(login).not.toHaveBeenCalled();
  });

  it('reports an authentication request error and clears the busy state', async () => {
    const requestError = new Error('network unavailable');
    login.mockRejectedValue(requestError);
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const component = new LoginComponent(
      { navigate } as unknown as Router,
      { login } as unknown as AuthSessionService
    );
    component.username = 'student';
    component.password = 'test-password';

    await component.login();

    expect(component.message).toContain('network unavailable');
    expect(component.busy).toBe(false);
    expect(consoleError).toHaveBeenCalledWith(requestError);
  });
});
