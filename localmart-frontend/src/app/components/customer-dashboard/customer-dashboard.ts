import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { ShopService } from '../../services/shop';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms'; 
import { DatePipe } from '@angular/common'; 

@Component({
  selector: 'app-customer-dashboard',
  standalone: true,
  imports: [FormsModule,DatePipe], 
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
  deliveryAddress: string = ''; 

  cart: any[] = [];
  cartVendorId: number | null = null;
  cartVendorName: string = '';
  deliveryFee: number = 0;
  freeDeliveryThreshold: number = 0;
  orderType: string = 'DELIVERY'; 

   pollItems: any[] = [];
  selectedPollItems: Set<number> = new Set<number>();

  showReviewModal: boolean = false;
  reviewOrderId: number | null = null;
  reviewRating: number = 5;
  reviewText: string = '';

  ngOnInit() {
    this.loadProfile();
    this.loadLocalShops();
    this.loadOrders();
    this.loadPollItems();
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

    if (this.orderType === 'DELIVERY' && !this.deliveryAddress.trim()) {
   alert('Please enter a delivery address.');
   return;
}



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
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('role');
    this.router.navigate(['/login']); 
  }

    

   loadPollItems() {
    this.shopService.getPollItems().subscribe({
      next: (data) => {
        this.pollItems = data;
        this.cdr.detectChanges();
      },
      error: (err) => console.error('Failed to load poll items', err)
    });
  }

  togglePollItem(itemId: number, event: any) {
    if (event.target.checked) {
      this.selectedPollItems.add(itemId);
    } else {
      this.selectedPollItems.delete(itemId);
    }
  }

  submitVote() {
    if (this.selectedPollItems.size === 0) {
      alert("Please select at least one item to vote!");
      return;
    }
    const itemIds = Array.from(this.selectedPollItems);
    const pincode = this.customerProfile ? this.customerProfile.pincode : '000000';
    
    this.shopService.submitPollVote(itemIds, pincode).subscribe({
      next: (res) => alert('Your votes have been recorded! Thank you for participating.'),
      error: (err) => alert('Failed to submit votes.')
    });
  }

  confirmDelivery(order: any) {
    this.shopService.confirmDelivery(order.id).subscribe({
      next: (res) => {
        this.loadOrders(); // Refresh order history instantly
        
        // Pop open the review modal for this specific order
        this.reviewOrderId = order.id;
        this.reviewRating = 5; 
        this.reviewText = '';
        this.showReviewModal = true; 
      },
      error: (err) => alert('Failed to confirm delivery.')
    });
  }

  submitReview() {
    if (!this.reviewOrderId) return;
    
    const payload = {
      order: this.reviewOrderId,
      rating: Number(this.reviewRating), // Ensure it is sent as a number
      text: this.reviewText
    };
    
    this.shopService.submitReview(payload).subscribe({
      next: (res) => {
        alert('Thank you for your review!');
        this.closeReviewModal();
        this.loadLocalShops(); // Refresh shops so the new score will eventually appear
      },
      error: (err) => {
        alert('Failed to submit review. You may have already reviewed this order.');
        console.error(err);
      }
    });
  }
  
  closeReviewModal() {
    this.showReviewModal = false;
    this.reviewOrderId = null;
  }

  
}
