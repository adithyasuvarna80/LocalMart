import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { ShopService } from '../../services/shop';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms'; 

@Component({
  selector: 'app-customer-dashboard',
  standalone: true,
  imports: [FormsModule], 
  templateUrl: './customer-dashboard.html',
  styleUrl: './customer-dashboard.css',
})
export class CustomerDashboard implements OnInit {
  private shopService = inject(ShopService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);

  customerProfile: any = null; 
  shops: any[] = [];
  orders: any[] = []; 
  isLoading: boolean = true;

  cart: any[] = [];
  cartVendorId: number | null = null;
  cartVendorName: string = '';
  deliveryFee: number = 0;
  freeDeliveryThreshold: number = 0;
  orderType: string = 'DELIVERY'; 

  ngOnInit() {
    this.loadProfile();
    this.loadLocalShops();
    this.loadOrders();
  }

  loadProfile() {
    this.shopService.getCustomerProfile().subscribe({
      next: (data) => {
        this.customerProfile = data;
        this.cdr.detectChanges();
      },
      error: (err) => console.error('Failed to load profile', err)
    });
  }

  loadLocalShops() {
    this.shopService.getLocalShops().subscribe({
      next: (data) => {
        
        this.shops = data.map(shop => {
          shop.today_stock = shop.today_stock.map((item: any) => ({
            ...item,
            selectedQty: 1 
          }));
          return shop;
        });
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Failed to load local shops', err);
        this.isLoading = false;
      }
    });
  }

  loadOrders() {
    this.shopService.getOrders().subscribe({
      next: (data) => {
        this.orders = data;
        this.cdr.detectChanges();
      },
      error: (err) => console.error('Failed to load orders', err)
    });
  }


  addToCart(shop: any, item: any) {
    if (item.selectedQty <= 0 || item.selectedQty > parseFloat(item.quantity)) {
      alert("Please enter a valid quantity within the available stock.");
      return;
    }

    if (this.cart.length > 0 && this.cartVendorId !== shop.id) {
      alert("You can only order from one shop at a time. Please clear your cart first.");
      return;
    }

    this.cartVendorId = shop.id;
    this.cartVendorName = shop.shop_name;
    this.deliveryFee = parseFloat(shop.delivery_fee);
    this.freeDeliveryThreshold = parseFloat(shop.free_delivery_threshold);

    const existingItem = this.cart.find(c => c.product === item.product);
    
    if (existingItem) {
      if (existingItem.cartQty + item.selectedQty <= parseFloat(item.quantity)) {
        existingItem.cartQty += item.selectedQty;
      } else {
        alert("You cannot add more than the vendor's available stock!");
      }
    } else {
      this.cart.push({
        product: item.product,
        product_name: item.product_name,
        price: parseFloat(item.base_price),
        cartQty: item.selectedQty
      });
    }

    item.selectedQty = 1; 
    this.cdr.detectChanges();
  }

  clearCart() {
    this.cart = [];
    this.cartVendorId = null;
    this.cdr.detectChanges();
  }

  get subtotal() {
    return this.cart.reduce((sum, item) => sum + (item.price * item.cartQty), 0);
  }

  get finalDeliveryFee() {
    if (this.orderType === 'PICKUP') return 0;
    return this.subtotal >= this.freeDeliveryThreshold ? 0 : this.deliveryFee;
  }

  get totalAmount() {
    return this.subtotal + this.finalDeliveryFee;
  }

  checkout() {
    if (this.cart.length === 0) return;

    const orderData = {
      vendor: this.cartVendorId,
      order_type: this.orderType,
      subtotal: this.subtotal,
      delivery_fee: this.finalDeliveryFee,
      total_amount: this.totalAmount,
      items: this.cart.map(item => ({
        product: item.product,
        quantity: item.cartQty,
        price: item.price
      }))
    };

    this.shopService.placeOrder(orderData).subscribe({
      next: (res) => {
        alert('Order placed successfully!');
        this.clearCart();
        this.loadLocalShops(); 
        this.loadOrders(); 
      },
      error: (err) => {
        alert('Failed to place order.');
        console.error(err);
      }
    });
  }

  logout() {
    localStorage.clear();
    this.router.navigate(['/login']);
  }
}
