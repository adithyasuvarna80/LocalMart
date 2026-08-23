import { Component, OnInit, inject,ChangeDetectorRef } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ShopService } from '../../services/shop';
import { Router } from '@angular/router';
import Chart from 'chart.js/auto';
import { DatePipe } from '@angular/common';
import { CommonModule } from '@angular/common';
@Component({
  selector: 'app-vendor-dashboard',
  standalone: true,
  imports: [ReactiveFormsModule,DatePipe,CommonModule],
  templateUrl: './vendor-dashboard.html',
  styleUrl: './vendor-dashboard.css',
})
export class VendorDashboard implements OnInit {
  private fb = inject(FormBuilder);
  private shopService = inject(ShopService);
  private router = inject(Router);
   private cdr = inject(ChangeDetectorRef);

  needsStockUpdate: boolean = true; 
  dailyStock: any[] = [];
   orders: any[] = [];
   chart: any;

   activeTab: string = 'live-stock';


  isClosedToday: boolean = false;

  products: any[] = [];
  reviews: any[] = [];
  
  vendorProfile: any = {
    shop_name: 'Loading...',
    locality: 'Loading...',
    pincode: '---',
    platform_score: '0.0'
  };

   userEmail: string = 'vendor@localmart.com';

  productForm = this.fb.group({
    name: ['', Validators.required],
    unit: ['KG', Validators.required],
    base_price: ['', [Validators.required, Validators.min(1)]]
  });

  

  ngOnInit() {
    this.loadProducts();
    this.loadProfile(); 
    this.loadDailyStock();
    this.loadOrders(); 
    this.loadChartData();
  }

    saveLiveStock() {
    this.shopService.updateDailyStock(this.dailyStock).subscribe({
      next: (res) => {
        // 1. Ensure localStorage is updated for today
        const today = new Date().toISOString().split('T')[0];
        localStorage.setItem('last_stock_submit', today);

        // 2. Reload both stock levels AND the profile state (clears the nudge in UI!)
        this.loadDailyStock();
        this.loadProfile(); 
        
        this.cdr.detectChanges();
        alert('Live stock updated successfully! ✅');
      },
      error: (err) => {
        alert('Failed to update live stock.');
        console.error(err);
      }
    });
  }


  
  toggleShopClosed() {
   this.shopService.toggleShopClosed().subscribe({
      next: (res) => {
        this.isClosedToday = res.is_closed_today;
        this.cdr.detectChanges();

        if (this.isClosedToday) {
          this.needsStockUpdate = false; 
        }
      },
      
      error: (err) => {
        alert('Failed to update shop status.');
        console.error(err);
      }
    });
  }


     loadDailyStock() { 
    this.shopService.getDailyStock().subscribe({ 
      next: (data) => { 
        this.dailyStock = data; 
        
        // 1. Bypass gate if catalog is empty, or if the shop is marked closed today
        if (this.dailyStock.length === 0 || this.isClosedToday) { 
          this.needsStockUpdate = false; 
        } 
        else {
          const today = new Date().toISOString().split('T')[0];
          const lastSubmit = localStorage.getItem('last_stock_submit'); 
          
          // 2. Bypass gate if stock has already been submitted today
          if (lastSubmit === today) {
            this.needsStockUpdate = false; 
          }
        }
        
        this.cdr.detectChanges(); 
      }, 
      error: (err) => console.error('Failed to load daily stock', err) 
    }); 
  }

 
  onQuantityChange(index: number, event: any) {
 
  this.dailyStock[index].quantity = parseFloat(event.target.value) || 0;
}
  
  onPriceChange(index: number, event: any) {
    const val = parseFloat(event.target.value);
    if (!isNaN(val) && val >= 0) {
      this.dailyStock[index].base_price = val;
    }
  }


 
   submitStock() {
    this.shopService.updateDailyStock(this.dailyStock).subscribe({
      next: (res) => {
        // 1. Record today's date to unlock the gate on refresh
        const today = new Date().toISOString().split('T')[0];
        localStorage.setItem('last_stock_submit', today);

        // 2. Dismiss the morning gate overlay
        this.needsStockUpdate = false;

        // 3. Reload both stock levels and profile details
        this.loadDailyStock();
        this.loadProfile(); // <-- CRITICAL: Dismisses nudge banner & registers open status
        
        this.cdr.detectChanges();
        alert('Morning stock saved successfully! Your shop is now open. 📦');
      },
      error: (err) => {
        alert('Failed to save morning stock.');
        console.error(err);
      }
    });
  }

   loadProducts() {
    this.shopService.getProducts().subscribe({
      next: (data) => {
        this.products = data;
        this.cdr.detectChanges(); 
      },
      error: (err) => console.error('Failed to load products', err)
    });
  }


  
  loadProfile() {
    this.shopService.getVendorProfile().subscribe({
      next: (data) => {
        this.vendorProfile = data;
        this.userEmail = data.email; 
        this.isClosedToday = data.is_closed_today; 
        this.cdr.detectChanges(); 
        this.loadReviews(data.id);
      },
      error: (err) => console.error('Failed to load profile', err)
    });
  }

  onSubmit() {
    if (this.productForm.valid) {
      this.shopService.addProduct(this.productForm.value).subscribe({
        next: (res) => {
          this.products.push(res);
          this.productForm.reset({ unit: 'KG' });
          this.loadDailyStock(); 
        },
        error: (err) => console.error(err)
      });
    }
  }

  deleteProduct(productId: number) {
    if (confirm('Are you sure you want to delete this product?')) {
      this.shopService.deleteProduct(productId).subscribe({
        next: () => {
          this.products = this.products.filter(p => p.id !== productId);
        },
        error: (err) => {
          alert('Failed to delete product.');
          console.error(err);
        }
      });
    }
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

  updateOrderStatus(orderId: number, status: string) {
    this.shopService.updateOrderStatus(orderId, status).subscribe({
      next: (res) => {
        this.loadOrders(); 
      },
      error: (err) => alert('Failed to update order status.')
    });
  }

   logout() { 
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('role');
    this.router.navigate(['/login']); 
  }
   loadChartData() {
    this.shopService.getPollChartData().subscribe({
      next: (data) => this.renderChart(data),
      error: (err) => console.error('Failed to load chart data', err)
    });
  }

  renderChart(data: any[]) {
    const labels = data.map(item => item.item_name);
    const votes = data.map(item => item.vote_count);

    // Destroy old chart instance if it exists to allow refreshing
    if (this.chart) {
      this.chart.destroy();
    }

    const ctx = document.getElementById('pollChart') as HTMLCanvasElement;
    if (!ctx) return;

    this.chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Number of Votes',
          data: votes,
          backgroundColor: 'rgba(54, 162, 235, 0.6)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1
            }
          }
        },
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }
  loadReviews(vendorId: number) {
  this.shopService.getVendorReviews(vendorId).subscribe({
    next: (data) => {

      console.log("Reviews received:", data);

      this.reviews = data;
      this.cdr.detectChanges();
    },
    error: (err) => console.error(err)
  });
}
    switchTab(tab: string) {
    this.activeTab = tab;
    this.cdr.detectChanges(); // 1. Force Angular to update the DOM immediately

    // 2. If switching to the demand poll tab, trigger the chart loader!
    if (tab === 'polls') {
      setTimeout(() => {
        this.loadChartData();
      }, 50); // A tiny 50ms delay guarantees the canvas element is fully active in the DOM
    }
  }

}
