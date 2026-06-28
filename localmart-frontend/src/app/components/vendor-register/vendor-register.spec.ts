import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VendorRegister } from './vendor-register';

describe('VendorRegister', () => {
  let component: VendorRegister;
  let fixture: ComponentFixture<VendorRegister>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VendorRegister],
    }).compileComponents();

    fixture = TestBed.createComponent(VendorRegister);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
