import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { ShopService } from '../../services/shop';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms'; 
import { DatePipe,DecimalPipe } from '@angular/common'; 
import { CommonModule } from '@angular/common';
import { ToastService, Toast } from '../../services/toast';

@Component({
  selector: 'app-customer-dashboard',
  standalone: true,
  imports: [FormsModule,DatePipe,DecimalPipe,CommonModule], 
  templateUrl: './customer-dashboard.html',
  styleUrl: './customer-dashboard.css',
})
export class CustomerDashboard implements OnInit {
  private shopService = inject(ShopService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
  private toast = inject(ToastService)


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

  walletBalance: number = 0;
walletTransactions: any[] = [];
tokensToUse: number = 0;
activeTab: string = 'shops'; 

starsArray: number[] = Array.from({ length: 5 }, (_, i) => i + 1);

  ngOnInit() {
    this.loadProfile();
    this.loadLocalShops();
    this.loadOrders();
    this.loadPollItems();
    this.loadWalletHistory();

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
      this.toast.warning("Please enter a valid quantity within the available stock.");
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
     this.toast.success(`Added ${item.selectedQty} ${item.unit} of ${item.name} to cart!`);
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
  get tokenDiscount() {
  return this.tokensToUse * 0.10; 
}

  get totalAmount() {
  const amt = this.subtotal + this.finalDeliveryFee - this.tokenDiscount;
  return amt < 0 ? 0 : amt;
}

  checkout() {
  if (this.cart.length === 0) return;
  
  if (this.orderType === 'DELIVERY' && !this.deliveryAddress.trim()) {
    this.toast.error('Please enter a delivery address.');
    return;
  }

  if (this.tokensToUse > this.walletBalance) {
    this.toast.error('You cannot redeem more tokens than your available balance.');
    return;
  }



const orderData = {
    vendor: this.cartVendorId,
    order_type: this.orderType,
    subtotal: this.subtotal,
    delivery_fee: this.finalDeliveryFee,
    tokens_used: this.tokensToUse, // <-- ADDED
    total_amount: this.totalAmount,
    delivery_address: this.deliveryAddress,
    items: this.cart.map(item => ({
      product: item.product,
      quantity: item.cartQty,
      price: item.price
    }))
  };

  this.shopService.placeOrder(orderData).subscribe({
    next: (res) => {
      this.toast.success(`Order placed successfully! Paid ₹${res.total_amount}.`);
      this.clearCart();
      this.tokensToUse = 0;
      this.deliveryAddress = '';
      this.loadOrders();
      this.loadWalletHistory(); // <-- Refresh wallet numbers immediately
    },
    error: (err) => {
      this.toast.error(err.error?.error || 'Failed to place order.');
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
    this.toast.error("Please select at least one item to vote!");
    return;
  }
  const itemIds = Array.from(this.selectedPollItems);
  const pincode = this.customerProfile ? this.customerProfile.pincode : '000000';

  this.shopService.submitPollVote(itemIds, pincode).subscribe({
    next: (res) => {
      this.toast.success("Your daily poll vote has been submitted successfully! 🪙 You have been entered into today's 11 PM Token Lottery!");
      this.selectedPollItems.clear();
      this.loadWalletHistory();
      this.cdr.detectChanges();
    },
    error: (err) => {
      this.toast.error("Failed to submit your vote.");
      console.error(err);
    }
  });
}

  confirmDelivery(order: any) {
    this.shopService.confirmDelivery(order.id).subscribe({
      next: (res) => {
        this.toast.success("Delivery confirmed! Thank you for shopping with LocalMart.");
        this.loadOrders();
          
        
        
        this.reviewOrderId = order.id;
        this.reviewRating = 5; 
        this.reviewText = '';
        this.showReviewModal = true; 
      },
      error: (err) => this.toast.error('Failed to confirm delivery.')
    });
  }

  submitReview() {
    if (!this.reviewOrderId) return;
    
    const payload = {
      order: this.reviewOrderId,
      rating: Number(this.reviewRating), 
      text: this.reviewText
    };
    
    this.shopService.submitReview(payload).subscribe({
      next: (res) => {
        this.toast.success('Thank you for your review!');
        this.closeReviewModal();
        this.loadLocalShops(); 
      },
      error: (err) => {
        this.toast.error('Failed to submit review. You may have already reviewed this order.');
        console.error(err);
      }
    });
  }
  
  closeReviewModal() {
    this.showReviewModal = false;
    this.reviewOrderId = null;
  }

  loadWalletHistory() {
  this.shopService.getWalletHistory().subscribe({
    next: (data) => {
      this.walletBalance = data.wallet_balance;
      this.walletTransactions = data.transactions;
      this.cdr.detectChanges();
    },
    error: (err) => console.error('Failed to load wallet data', err)
  });
}

  
}
