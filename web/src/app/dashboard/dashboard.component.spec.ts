import '@angular/compiler';
import { ChangeDetectorRef, NgZone } from '@angular/core';
import { Router } from '@angular/router';
import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthSessionService } from '../auth-session.service';
import { DashboardComponent } from './dashboard.component';
import { MemoryStorage } from '../../testing/memory-storage';

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}));

describe('DashboardComponent', () => {
  let storage: MemoryStorage;
  let navigate: ReturnType<typeof vi.fn>;
  let detectChanges: ReturnType<typeof vi.fn>;
  let getStoredSession: ReturnType<typeof vi.fn>;
  let clearSession: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    storage = new MemoryStorage();
    vi.stubGlobal('localStorage', storage);
    vi.clearAllMocks();
    navigate = vi.fn().mockResolvedValue(true);
    detectChanges = vi.fn();
    getStoredSession = vi.fn();
    clearSession = vi.fn();
  });

  it('loads tasks for a valid session using the bearer token', async () => {
    getStoredSession.mockReturnValue({
      kind: 'authenticated',
      session: { token: 'test-token', user: { username: 'student' } }
    });
    vi.mocked(axios.get).mockResolvedValue({ data: [] } as never);
    const zone = { run: (callback: () => void) => callback() };
    const component = new DashboardComponent(
      { navigate } as unknown as Router,
      { detectChanges } as unknown as ChangeDetectorRef,
      zone as unknown as NgZone,
      { getStoredSession, clearSession } as unknown as AuthSessionService
    );

    await component.ngOnInit();

    expect(axios.get).toHaveBeenCalledWith(
      'http://localhost:8000/api/tasks?owner=student',
      { headers: { Authorization: 'Bearer test-token' } }
    );
    expect(component.loading).toBe(false);
    expect(detectChanges).toHaveBeenCalled();
  });

  it('clears an invalid stored user and redirects without requesting tasks', async () => {
    getStoredSession.mockReturnValue({ kind: 'invalid-user' });
    const zone = { run: (callback: () => void) => callback() };
    const component = new DashboardComponent(
      { navigate } as unknown as Router,
      { detectChanges } as unknown as ChangeDetectorRef,
      zone as unknown as NgZone,
      { getStoredSession, clearSession } as unknown as AuthSessionService
    );

    await component.ngOnInit();

    expect(getStoredSession).toHaveBeenCalledOnce();
    expect(navigate).toHaveBeenCalledWith(['/login']);
    expect(axios.get).not.toHaveBeenCalled();
  });

  it('redirects when the token is missing', async () => {
    getStoredSession.mockReturnValue({ kind: 'missing-token' });
    const zone = { run: (callback: () => void) => callback() };
    const component = new DashboardComponent(
      { navigate } as unknown as Router,
      { detectChanges } as unknown as ChangeDetectorRef,
      zone as unknown as NgZone,
      { getStoredSession, clearSession } as unknown as AuthSessionService
    );

    await component.ngOnInit();

    expect(navigate).toHaveBeenCalledWith(['/login']);
    expect(axios.get).not.toHaveBeenCalled();
  });

  it('filters archived tasks, labels visible tasks, and handles known statuses', async () => {
    getStoredSession.mockReturnValue({
      kind: 'authenticated',
      session: { token: 'test-token', user: { username: 'student' } }
    });
    vi.mocked(axios.get).mockResolvedValue({
      data: [
        { title: 'Low task', status: 'TODO', priority: 'LOW', owner: 'student' },
        { title: 'Archived task', status: 'ARCHIVED', priority: 'HIGH', owner: 'student' },
        { title: 'High task', status: 'DONE', priority: 'HIGH', owner: 'student' }
      ]
    } as never);
    const zone = { run: (callback: () => void) => callback() };
    const component = new DashboardComponent(
      { navigate } as unknown as Router,
      { detectChanges } as unknown as ChangeDetectorRef,
      zone as unknown as NgZone,
      { getStoredSession, clearSession } as unknown as AuthSessionService
    );

    await component.ngOnInit();

    expect(component.visibleTasks.map((task) => task.title)).toEqual(['Low task', 'High task']);
    expect(component.visibleTasks.map((task) => task.label)).toEqual([
      'LOW · STUDENT',
      'HIGH · STUDENT'
    ]);
    expect(component.statusLabel('DONE')).toBe('Completado');
    expect(component.statusLabel('CUSTOM')).toBe('CUSTOM');
  });

  it('reports a task loading error and ends loading', async () => {
    getStoredSession.mockReturnValue({
      kind: 'authenticated',
      session: { token: 'test-token', user: { username: 'student' } }
    });
    vi.mocked(axios.get).mockRejectedValue({ message: 'network unavailable' });
    const zone = { run: (callback: () => void) => callback() };
    const component = new DashboardComponent(
      { navigate } as unknown as Router,
      { detectChanges } as unknown as ChangeDetectorRef,
      zone as unknown as NgZone,
      { getStoredSession, clearSession } as unknown as AuthSessionService
    );

    await component.ngOnInit();

    expect(component.error).toBe('network unavailable');
    expect(component.loading).toBe(false);
    expect(detectChanges).toHaveBeenCalled();
  });

  it('clears the session and navigates to login on logout', async () => {
    const zone = { run: (callback: () => void) => callback() };
    const component = new DashboardComponent(
      { navigate } as unknown as Router,
      { detectChanges } as unknown as ChangeDetectorRef,
      zone as unknown as NgZone,
      { getStoredSession, clearSession } as unknown as AuthSessionService
    );

    await component.logout();

    expect(clearSession).toHaveBeenCalledOnce();
    expect(navigate).toHaveBeenCalledWith(['/login']);
  });
});
