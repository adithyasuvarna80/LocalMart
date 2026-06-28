import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-login',
  standalone: true,
   imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);

  // A simple unified login form for both vendors and customers
  loginForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required]
  });

  onSubmit() {
    if (this.loginForm.valid) {
      this.authService.login(this.loginForm.value).subscribe({
        next: (res) => {
          // The backend returns an access token and a refresh token
          localStorage.setItem('access_token', res.access);
          localStorage.setItem('refresh_token', res.refresh);
          alert('Login successful!');
          
          // Note: We will add routing to the vendor/customer dashboards later
        },
        error: (err) => {
          alert('Login failed. Please check your credentials.');
          console.error(err);
        }
      });
    }
  }
}