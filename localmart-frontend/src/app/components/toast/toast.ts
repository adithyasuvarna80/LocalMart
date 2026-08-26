import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastService, Toast } from '../../services/toast';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './toast.html',
  styleUrl: './toast.css'
})
export class ToastComponent implements OnInit {
  private toastService = inject(ToastService);
  toasts$!: Observable<Toast[]>;

  ngOnInit() {
    this.toasts$ = this.toastService.getToasts();
  }

  remove(id: number) {
    this.toastService.remove(id);
  }
}
