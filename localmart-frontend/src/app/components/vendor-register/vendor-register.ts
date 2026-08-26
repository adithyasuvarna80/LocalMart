import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common'; // 👈 Enabled structural conditions
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-vendor-register',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    CommonModule // 👈 Enabled CommonModule for *ngIf and dropdown binds
  ],
  templateUrl: './vendor-register.html',
  styleUrl: './vendor-register.css'
})
export class VendorRegisterComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  isPasswordVisible: boolean = false; // 👈 Password visibility toggle

  vendorForm = this.fb.group({
    shop_name: ['', Validators.required],
    category: ['VEGETABLES', Validators.required],
    locality: ['', Validators.required],
    pincode: ['', [Validators.required,Validators.pattern(/^[1-9][0-9]{5}$/)]],
    delivery_fee: [0, [Validators.required, Validators.min(0)]],
    free_delivery_threshold: [0, [Validators.required, Validators.min(0)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]]
  });

  onSubmit() {
    if (this.vendorForm.valid) {
      this.authService.registerVendor(this.vendorForm.value).subscribe({
        next: (res) => {
          alert('Congratulations! Your vendor profile has been created successfully. You can now log in and set up your master product catalog!');
          this.router.navigate(['/login']);
        },
        error: (err) => {
          alert(err.error?.error || 'Registration failed. Please double-check your retail fields.');
          console.error(err);
        }
      });
    }
  }

  togglePasswordVisibility() {
    this.isPasswordVisible = !this.isPasswordVisible;
  }
}