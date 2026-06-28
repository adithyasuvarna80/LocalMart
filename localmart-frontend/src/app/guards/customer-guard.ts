import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const customerGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  const token = localStorage.getItem('access_token');
  const role = localStorage.getItem('role'); 

  if (token && role === 'CUSTOMER') {
    return true; // Let them pass
  }
  
  router.navigate(['/login']);
  return false; 
};