import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const vendorGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  const token = localStorage.getItem('access_token');
  const role = localStorage.getItem('role'); 

  if (token && role === 'VENDOR') {
    return true; // Let them pass
  }
  
  router.navigate(['/login']);
  return false; 
};