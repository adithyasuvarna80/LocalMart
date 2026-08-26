import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common'; // 👈 Enabled structural conditions
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-customer-register',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    CommonModule // 👈 Added CommonModule for *ngIf and validations
  ],
  templateUrl: './customer-register.html',
  styleUrl: './customer-register.css'
})
export class CustomerRegisterComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  isPasswordVisible: boolean = false; // 👈 Password visibility toggle

  customerForm = this.fb.group({
    name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    pincode: ['', [Validators.required, Validators.pattern(/^[1-9][0-9]{5}$/)]], // Checks standard 6-digit PIN
    area_name: ['', Validators.required]
  });

  onSubmit() {
    if (this.customerForm.valid) {
      this.authService.registerCustomer(this.customerForm.value).subscribe({
        next: (res) => {
          alert('Account created! Welcome to LocalMart. You can now log in using your registered credentials.');
          this.router.navigate(['/login']);
        },
        error: (err) => {
          alert(err.error?.error || 'Registration failed. Please double-check your fields.');
          console.error(err);
        }
      });
    }
  }

  togglePasswordVisibility() {
    this.isPasswordVisible = !this.isPasswordVisible;
  }
}