import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { Router, RouterLink } from '@angular/router'; // <-- Added Router here

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
  private router = inject(Router); // <-- Injecting the router

  loginForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required]
  });

  onSubmit() {
    if (this.loginForm.valid) {
      this.authService.login(this.loginForm.value).subscribe({
        next: (res) => {
          // Store tokens AND the newly added role
          localStorage.setItem('access_token', res.access);
          localStorage.setItem('refresh_token', res.refresh);
          localStorage.setItem('role', res.role);

          alert('Login successful!');

          // Automatically route the user based on their role
          if (res.role === 'VENDOR') {
            this.router.navigate(['/vendor']);
          } else if (res.role === 'CUSTOMER') {
            this.router.navigate(['/customer']);
          }
        },
        error: (err) => {
          alert('Login failed. Please check your credentials.');
          console.error(err);
        }
      });
    }
  }
}