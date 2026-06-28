import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  // URL of the Django backend
  private apiUrl = 'http://localhost:8000/api/auth';

  // Vendor Registration Flow
  registerVendor(vendorData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/register/vendor/`, vendorData);
  }

  // Customer Registration Flow
  registerCustomer(customerData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/register/customer/`, customerData);
  }

  // Login Flow (Returns JWT Tokens)
  login(credentials: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/login/`, credentials);
  }
}