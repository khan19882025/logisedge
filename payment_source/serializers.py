from rest_framework import serializers
from .models import PaymentSource
from chart_of_accounts.models import ChartOfAccount
from multi_currency.models import Currency
from customer.models import Customer


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = 'auth.User'
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class ChartOfAccountSerializer(serializers.ModelSerializer):
    """Serializer for ChartOfAccount model"""
    
    class Meta:
        model = ChartOfAccount
        fields = ['id', 'account_code', 'name', 'account_type', 'account_nature']


class CurrencySerializer(serializers.ModelSerializer):
    """Serializer for Currency model"""
    
    class Meta:
        model = Currency
        fields = ['id', 'code', 'name', 'symbol']


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model (for vendors)"""
    
    class Meta:
        model = Customer
        fields = ['id', 'customer_code', 'customer_name']


class PaymentSourceSerializer(serializers.ModelSerializer):
    """Main serializer for PaymentSource model"""
    
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    linked_ledger = ChartOfAccountSerializer(read_only=True)
    default_expense_ledger = ChartOfAccountSerializer(read_only=True)
    default_vendor = CustomerSerializer(read_only=True)
    currency = CurrencySerializer(read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    linked_account_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = PaymentSource
        fields = [
            'id', 'name', 'code', 'description', 'payment_type', 'payment_type_display',
            'source_type', 'source_type_display', 'category', 'category_display',
            'currency', 'linked_ledger', 'default_expense_ledger', 'default_vendor',
            'active', 'remarks', 'linked_account', 'linked_account_display',
            'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class PaymentSourceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating PaymentSource"""
    
    class Meta:
        model = PaymentSource
        fields = [
            'name', 'code', 'description', 'payment_type', 'source_type', 'category',
            'currency', 'linked_ledger', 'default_expense_ledger', 'default_vendor',
            'active', 'remarks'
        ]
    
    def validate_name(self, value):
        """Validate that name is unique"""
        if PaymentSource.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A payment source with this name already exists.")
        return value
    
    def validate_code(self, value):
        """Validate that code is unique if provided"""
        if value and PaymentSource.objects.filter(code__iexact=value).exists():
            raise serializers.ValidationError("A payment source with this code already exists.")
        return value
    
    def validate_linked_ledger(self, value):
        """Validate that linked_ledger exists in Chart of Accounts"""
        if not value:
            raise serializers.ValidationError("Linked ledger is required.")
        
        if not ChartOfAccount.objects.filter(id=value.id, is_active=True).exists():
            raise serializers.ValidationError("Selected ledger account does not exist or is not active.")
        
        return value
    
    def validate(self, data):
        """Additional validation"""
        payment_type = data.get('payment_type')
        source_type = data.get('source_type')
        linked_ledger = data.get('linked_ledger')
        
        # Validate source_type matches payment_type for consistency
        if payment_type and source_type:
            if payment_type == 'prepaid' and source_type != 'prepaid':
                raise serializers.ValidationError(
                    "Source type should match payment type for consistency."
                )
            elif payment_type == 'postpaid' and source_type != 'postpaid':
                raise serializers.ValidationError(
                    "Source type should match payment type for consistency."
                )
        
        # If linked_ledger is not provided, try to get default
        if not linked_ledger:
            # Try to get default linked account
            temp_instance = PaymentSource(payment_type=payment_type)
            default_account = temp_instance.get_default_linked_account()
            if default_account:
                data['linked_ledger'] = default_account
            else:
                raise serializers.ValidationError(
                    "Please select a linked ledger or ensure appropriate accounts exist in Chart of Accounts."
                )
        
        return data


class PaymentSourceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating PaymentSource"""
    
    class Meta:
        model = PaymentSource
        fields = [
            'name', 'code', 'description', 'payment_type', 'source_type', 'category',
            'currency', 'linked_ledger', 'default_expense_ledger', 'default_vendor',
            'active', 'remarks'
        ]
    
    def validate_name(self, value):
        """Validate that name is unique (excluding current instance)"""
        instance = self.instance
        if PaymentSource.objects.filter(name__iexact=value).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError("A payment source with this name already exists.")
        return value
    
    def validate_code(self, value):
        """Validate that code is unique if provided (excluding current instance)"""
        if value:
            instance = self.instance
            if PaymentSource.objects.filter(code__iexact=value).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError("A payment source with this code already exists.")
        return value
    
    def validate_linked_ledger(self, value):
        """Validate that linked_ledger exists in Chart of Accounts"""
        if not value:
            raise serializers.ValidationError("Linked ledger is required.")
        
        if not ChartOfAccount.objects.filter(id=value.id, is_active=True).exists():
            raise serializers.ValidationError("Selected ledger account does not exist or is not active.")
        
        return value
    
    def validate(self, data):
        """Additional validation"""
        payment_type = data.get('payment_type')
        source_type = data.get('source_type')
        linked_ledger = data.get('linked_ledger')
        
        # Validate source_type matches payment_type for consistency
        if payment_type and source_type:
            if payment_type == 'prepaid' and source_type != 'prepaid':
                raise serializers.ValidationError(
                    "Source type should match payment type for consistency."
                )
            elif payment_type == 'postpaid' and source_type != 'postpaid':
                raise serializers.ValidationError(
                    "Source type should match payment type for consistency."
                )
        
        # If linked_ledger is not provided, try to get default
        if not linked_ledger:
            # Try to get default linked account
            instance = self.instance
            if instance:
                instance.payment_type = payment_type
                default_account = instance.get_default_linked_account()
                if default_account:
                    data['linked_ledger'] = default_account
                else:
                    raise serializers.ValidationError(
                        "Please select a linked ledger or ensure appropriate accounts exist in Chart of Accounts."
                    )
        
        return data


class PaymentSourceListSerializer(serializers.ModelSerializer):
    """Serializer for listing PaymentSource (minimal fields)"""
    
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    linked_account_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = PaymentSource
        fields = [
            'id', 'name', 'code', 'description', 'payment_type', 'payment_type_display',
            'source_type', 'source_type_display', 'category', 'category_display',
            'linked_account_display', 'active', 'created_at', 'updated_at'
        ]


class PaymentSourceDropdownSerializer(serializers.ModelSerializer):
    """Serializer for dropdown/select components"""
    
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    linked_account_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = PaymentSource
        fields = [
            'id', 'name', 'code', 'payment_type', 'payment_type_display', 
            'source_type', 'source_type_display', 'category', 'category_display',
            'linked_account_display', 'active'
        ]
