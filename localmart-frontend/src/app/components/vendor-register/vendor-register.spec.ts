import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VendorRegisterComponent } from './vendor-register';

describe('VendorRegister', () => {
  let component: VendorRegisterComponent;
  let fixture: ComponentFixture<VendorRegisterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VendorRegisterComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(VendorRegisterComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
