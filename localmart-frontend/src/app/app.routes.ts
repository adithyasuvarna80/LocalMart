import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { VendorRegisterComponent } from './components/vendor-register/vendor-register';
import { CustomerRegisterComponent } from './components/customer-register/customer-register';
import { vendorGuard } from './guards/vendor-guard';
import { customerGuard } from './guards/customer-guard';

export const routes: Routes = [
  // Public Routes
  { path: 'login', component: LoginComponent },
  { path: 'register/vendor', component: VendorRegisterComponent },
  { path: 'register/customer', component: CustomerRegisterComponent },
  
  // Protected Routes (We will build these dashboards in the next module)
  // The 'canActivate' array is what enforces the role guards!
  { 
    path: 'vendor', 
    loadComponent: () => import('./components/vendor-dashboard/vendor-dashboard').then(m => m.VendorDashboard),
    canActivate: [vendorGuard]
  },
  { 
    path: 'customer', 
    loadComponent: () => import('./components/customer-dashboard/customer-dashboard').then(m => m.CustomerDashboard),
    canActivate: [customerGuard]
  },

  // Default Route
  { path: '', redirectTo: '/login', pathMatch: 'full' }
];