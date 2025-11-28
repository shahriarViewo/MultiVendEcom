from rest_framework import permissions
from guardian.shortcuts import get_objects_for_user
from .models import VendorStaff

class IsVendorOwnerOrStaff(permissions.BasePermission):
    """
    Allows access if user is the Main Vendor Owner OR 
    if they are Staff with the specific required permission (e.g. 'edit_inventory').
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # 1. Check if User is the Main Owner of the object's vendor
        if hasattr(request.user, 'owned_vendor') and request.user.owned_vendor == obj.vendor:
            return True

        # 2. Check if User is Staff with specific permission
        # (We assume the view defines 'required_vendor_perm')
        required_perm = getattr(view, 'required_vendor_perm', None)
        
        if required_perm:
            # Check if user is linked to this vendor as staff
            try:
                staff_record = request.user.staff_assignments.get(vendor=obj.vendor)
                # Check if their role has the specific permission
                has_perm = staff_record.staff_role.permissions.filter(
                    vendor_permission__codename=required_perm
                ).exists()
                return has_perm
            except VendorStaff.DoesNotExist:
                return False
        
        return False
