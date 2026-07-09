import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-customer-register',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './customer-register.html',
  styleUrl: './customer-register.css'
})
export class CustomerRegisterComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);


  customerForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
    pincode: ['', Validators.required],
    area_name: ['', Validators.required]
  });

  onSubmit() {
    if (this.customerForm.valid) {
      this.authService.registerCustomer(this.customerForm.value).subscribe({
        next: (res) => {
          alert('Customer successfully registered! You can now log in to see your local shops.');
          this.customerForm.reset();
        },
        error: (err) => {
          alert('Registration failed. Please check your details.');
          console.error(err);
        }
      });
    }
  }
}