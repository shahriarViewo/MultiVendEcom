from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

# --- USER MANAGER ---
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

# --- CUSTOM USER ---
class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    banned = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

# --- LAYER 1: PLATFORM RBAC ---
class PlatformRole(models.Model):
    name = models.CharField(max_length=50, unique=True) # e.g. 'SuperAdmin', 'Support'
    description = models.TextField(blank=True)
    def __str__(self): return self.name

class PlatformPermission(models.Model):
    codename = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255)
    def __str__(self): return self.codename

class UserRole(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='platform_roles')
    role = models.ForeignKey(PlatformRole, on_delete=models.CASCADE)
    class Meta: unique_together = ('user', 'role')

class RolePermission(models.Model):
    role = models.ForeignKey(PlatformRole, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(PlatformPermission, on_delete=models.CASCADE)
    class Meta: unique_together = ('role', 'permission')

# --- LAYER 2: VENDOR & STAFF RBAC ---
class Vendor(models.Model):
    owner_user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='owned_vendor')
    store_name = models.CharField(max_length=255, unique=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.store_name

class VendorPermission(models.Model):
    codename = models.CharField(max_length=100, unique=True) # e.g. 'edit_inventory'
    description = models.CharField(max_length=255)
    def __str__(self): return self.codename

class VendorStaffRole(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='staff_roles')
    name = models.CharField(max_length=50)
    class Meta: unique_together = ('vendor', 'name')
    def __str__(self): return f"{self.name} @ {self.vendor.store_name}"

class VendorStaffRolePermission(models.Model):
    staff_role = models.ForeignKey(VendorStaffRole, on_delete=models.CASCADE, related_name='permissions')
    vendor_permission = models.ForeignKey(VendorPermission, on_delete=models.CASCADE)
    class Meta: unique_together = ('staff_role', 'vendor_permission')

class VendorStaff(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='staff_assignments')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='staff_members')
    staff_role = models.ForeignKey(VendorStaffRole, on_delete=models.CASCADE)
    class Meta: unique_together = ('user', 'vendor')

# --- E-COMMERCE MODELS ---
class Product(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    customer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='orders')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class VendorOrder(models.Model):
    master_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='vendor_sub_orders')
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='orders')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    class Meta: unique_together = ('master_order', 'vendor')
