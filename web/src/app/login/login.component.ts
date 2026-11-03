import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import merge from 'lodash/merge';
import { AuthSessionService } from '../auth-session.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  username: any = '';
  password: any = '';
  busy: any = false;
  message: any = '';
  preferences: any = { theme: 'light', showTips: true, compact: false };

  constructor(private router: Router, private authSession: AuthSessionService) {
    try {
      const saved = JSON.parse(localStorage.getItem('workshop_preferences') || '{}');
      this.preferences = merge(this.preferences, saved);
    } catch (error) {
      console.log('Preferences could not be loaded', error);
    }
  }

  async login(): Promise<void> {
    this.message = '';
    if (this.username === null || this.username === undefined || String(this.username).trim() === '') {
      this.message = '<strong>Ingrese un usuario.</strong>';
    } else {
      if (this.password === null || this.password === undefined || String(this.password).trim() === '') {
        this.message = '<strong>Ingrese una contraseña.</strong>';
      } else {
        this.busy = true;
        try {
          const result = await this.authSession.login(this.username, this.password);
          if (result.kind === 'authenticated') {
            localStorage.setItem('workshop_preferences', JSON.stringify(this.preferences));
            await this.router.navigate(['/dashboard']);
          } else if (result.kind === 'missing-token') {
            this.message = '<strong>El backend respondió sin token.</strong>';
          } else {
            this.message = '<strong>El backend respondió sin un usuario válido.</strong>';
          }
        } catch (error: any) {
          const backendMessage = error?.response?.data?.message || error?.message || 'Error desconocido';
          this.message = '<strong>No se pudo autenticar a ' + this.username + '.</strong><br>' + backendMessage;
          console.error(error);
        } finally {
          this.busy = false;
        }
      }
    }
  }
}
