from django.contrib import admin
from .models import *

# Register basic models to see them in /admin
admin.site.register(CustomUser)
admin.site.register(Vendor)
admin.site.register(Product)

# Register RBAC models
admin.site.register(PlatformRole)
admin.site.register(PlatformPermission)
admin.site.register(VendorStaffRole)
admin.site.register(VendorPermission)
admin.site.register(VendorStaff)
