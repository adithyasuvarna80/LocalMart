import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface Toast {
  id: number;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private toasts$ = new BehaviorSubject<Toast[]>([]);
  private counter = 0;

  getToasts() {
    return this.toasts$.asObservable();
  }

  show(type: 'success' | 'error' | 'warning' | 'info', message: string, duration = 4000) {
    const id = this.counter++;
    const newToast: Toast = { id, type, message, duration };
    this.toasts$.next([...this.toasts$.value, newToast]);

    setTimeout(() => {
      this.remove(id);
    }, duration);
  }

  success(message: string, duration = 4000) {
    this.show('success', message, duration);
  }

  error(message: string, duration = 4000) {
    this.show('error', message, duration);
  }

  warning(message: string, duration = 4000) {
    this.show('warning', message, duration);
  }

  info(message: string, duration = 4000) {
    this.show('info', message, duration);
  }

  remove(id: number) {
    this.toasts$.next(this.toasts$.value.filter(t => t.id !== id));
  }
}
