import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common'; // 👈 Enabled structural conditions
import { Router, RouterLink } from '@angular/router';
import { ToastService } from '../../services/toast'
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    ReactiveFormsModule, 
    RouterLink, 
    CommonModule 
  ],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private toast = inject(ToastService);

  isPasswordVisible: boolean = false; // 👈 Password toggle logic

  loginForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required]
  });

  onSubmit() {
    if (this.loginForm.valid) {
      this.authService.login(this.loginForm.value).subscribe({
        next: (res) => {
          localStorage.setItem('access_token', res.access);
          localStorage.setItem('refresh_token', res.refresh);
          localStorage.setItem('role', res.role);

          this.toast.success('Welcome back to LocalMart! Logged in successfully.');

          // Role-based routing logic [4]
          if (res.role === 'VENDOR') {
            this.router.navigate(['/vendor']);
          } else if (res.role === 'CUSTOMER') {
            this.router.navigate(['/customer']);
          }
        },
        error: (err) => {
          this.toast.error('Authentication failed. Please verify your email and password.');
          console.error(err);
        }
      });
    }
  }

  togglePasswordVisibility() {
    this.isPasswordVisible = !this.isPasswordVisible;
  }
}
