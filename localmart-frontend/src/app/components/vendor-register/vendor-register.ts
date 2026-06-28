import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-vendor-register',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './vendor-register.html',
  styleUrl: './vendor-register.css'
})
export class VendorRegisterComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);

  // Building the form with the exact fields from the synopsis
  vendorForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
    shop_name: ['', Validators.required],
    category: ['VEGETABLES', Validators.required], 
    locality: ['', Validators.required],
    pincode: ['', Validators.required],
    delivery_fee: [0, Validators.required],
    free_delivery_threshold: [0, Validators.required]
  });

  onSubmit() {
    if (this.vendorForm.valid) {
      this.authService.registerVendor(this.vendorForm.value).subscribe({
        next: (res) => {
          alert('Vendor successfully registered! You can now log in.');
          this.vendorForm.reset();
        },
        error: (err) => {
          alert('Registration failed. Please check your details.');
          console.error(err);
        }
      });
    }
  }
}