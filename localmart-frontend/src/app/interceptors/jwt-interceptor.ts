import { HttpInterceptorFn } from '@angular/common/http';

export const jwtInterceptor: HttpInterceptorFn = (req, next) => {
  // Retrieve the access token from local storage
  const token = localStorage.getItem('access_token');

  // ONLY attach the token if it exists AND the URL does NOT contain '/api/auth/'
  if (token && !req.url.includes('/api/auth/')) {
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  // Pass the request to the next step
  return next(req);
};