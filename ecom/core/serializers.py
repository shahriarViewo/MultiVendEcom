from rest_framework import serializers
from .models import CustomUser, Vendor, Product, Order, VendorOrder

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer to handle user registration. 
    It ensures the password is hashed correctly using the CustomUserManager.
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'name', 'password', 'phone')

    def create(self, validated_data):
        # Use the create_user helper to handle password hashing
        user = CustomUser.objects.create_user(**validated_data)
        return user

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        # IMPORTANT: Vendor is set automatically by the View logic (perform_create).
        # We make it read_only so the API user cannot inject a fake vendor ID.
        read_only_fields = ('vendor',) 
