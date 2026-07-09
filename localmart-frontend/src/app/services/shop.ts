import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ShopService {


  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/api/shop'; 

  getProducts(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/products/`);
  }

  addProduct(productData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/products/`, productData);
  }


  deleteProduct(productId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/products/${productId}/`);
  }

  
  getVendorProfile(): Observable<any> {
    return this.http.get(`${this.apiUrl}/profile/`);
  }

  getDailyStock(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/daily-stock/`);
  }

  
  updateDailyStock(stockData: any[]): Observable<any> {
    return this.http.post(`${this.apiUrl}/daily-stock/`, stockData);
  }

  toggleShopClosed(): Observable<any> {
    return this.http.post(`${this.apiUrl}/toggle-closed/`, {});
  }

  getLocalShops(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/local-shops/`);
  }

   placeOrder(orderData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/orders/place/`, orderData);
  }

  getOrders(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/orders/`);
  }

  getCustomerProfile(): Observable<any> {
    return this.http.get(`${this.apiUrl}/customer-profile/`);
  }
}


