import { Component, OnInit, inject,ChangeDetectorRef } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ShopService } from '../../services/shop';
import { Router } from '@angular/router';

@Component({
  selector: 'app-vendor-dashboard',
  standalone: true,
  imports: [ReactiveFormsModule],
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

  isClosedToday: boolean = false;

  products: any[] = [];
  
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
  }

  saveLiveStock() {
    this.shopService.updateDailyStock(this.dailyStock).subscribe({
      next: (res) => {
        alert('Live stock updated successfully!');
        this.cdr.detectChanges();
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
       
        if (this.dailyStock.length === 0) {
          this.needsStockUpdate = false;
        }
        this.cdr.detectChanges();
      },
      error: (err) => console.error('Failed to load daily stock', err)
    });
  }

 
  onQuantityChange(index: number, event: any) {
    this.dailyStock[index].quantity = Number(event.target.value);
  }


 
  submitStock() {
    this.shopService.updateDailyStock(this.dailyStock).subscribe({
      next: (res) => {
        this.needsStockUpdate = false; 
        this.cdr.detectChanges();
      },
      error: (err) => {
        alert('Failed to update stock. Please try again.');
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

  logout() {
    localStorage.clear();
    this.router.navigate(['/login']);
  }
}
