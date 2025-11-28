from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Product, Vendor
from .serializers import ProductSerializer, UserRegistrationSerializer
from .permissions import IsVendorOwnerOrStaff

# --- REGISTRATION VIEW ---
class RegisterView(generics.CreateAPIView):
    """
    Endpoint for users to register a new account.
    """
    serializer_class = UserRegistrationSerializer


# --- PRODUCT VIEWSET (RBAC ENFORCED) ---
class ProductViewSet(viewsets.ModelViewSet):
    """
    Handles Creating, Reading, Updating, and Deleting Products.
    Enforces RBAC so users only see/edit their own Vendor's products.
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsVendorOwnerOrStaff]
    
    # This string matches the 'codename' in your VendorPermission model
    # It tells the permission class: "To do unsafe things here, you need 'manage_products' permission"
    required_vendor_perm = 'manage_products' 

    def get_queryset(self):
        """
        Filter products based on who the user is.
        """
        user = self.request.user
        
        # 1. Superuser sees all products
        if user.is_superuser:
            return Product.objects.all()
            
        # 2. Vendor Owner sees their own products
        if hasattr(user, 'owned_vendor'):
            return Product.objects.filter(vendor=user.owned_vendor)
            
        # 3. Vendor Staff sees products of their assigned vendor
        # We look up the 'staff_assignments' related_name from the VendorStaff model
        staff_vendors = user.staff_assignments.values_list('vendor', flat=True)
        if staff_vendors:
            return Product.objects.filter(vendor__in=staff_vendors)
            
        # 4. Fallback: return nothing
        return Product.objects.none()

    def perform_create(self, serializer):
        """
        Automatically assign the new product to the correct Vendor.
        """
        user = self.request.user

        # Case A: User is the Main Vendor Owner
        if hasattr(user, 'owned_vendor'):
             serializer.save(vendor=user.owned_vendor)
             return

        # Case B: User is Vendor Staff
        # Fetch the staff record to find out which vendor they work for
        staff_assignment = user.staff_assignments.first() 
        
        if staff_assignment:
            # Assign the product to that staff member's vendor
            serializer.save(vendor=staff_assignment.vendor)
        else:
            # Case C: User is neither Owner nor Staff
            # (The permission class usually catches this, but this is a safety net)
            raise PermissionDenied("You must be associated with a Vendor to create products.")
