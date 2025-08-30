from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Vendor, Bill, BillHistory, BillReminder


class VendorSerializer(serializers.ModelSerializer):
    """Serializer for Vendor model"""
    
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'email', 'phone', 'address', 'tax_id', 
                 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value):
        """Validate email format"""
        if value and not '@' in value:
            raise serializers.ValidationError("Enter a valid email address.")
        return value


class BillHistorySerializer(serializers.ModelSerializer):
    """Serializer for BillHistory model"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = BillHistory
        fields = ['id', 'action', 'user', 'user_name', 'timestamp', 
                 'description', 'old_values', 'new_values']
        read_only_fields = ['id', 'user', 'user_name', 'timestamp']


class BillReminderSerializer(serializers.ModelSerializer):
    """Serializer for BillReminder model"""
    
    class Meta:
        model = BillReminder
        fields = ['id', 'reminder_type', 'sent_at', 'email_sent', 'notes']
        read_only_fields = ['id', 'sent_at']


class BillSerializer(serializers.ModelSerializer):
    """Serializer for Bill model"""
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)
    currency_name = serializers.CharField(source='currency.name', read_only=True)
    history = BillHistorySerializer(many=True, read_only=True)
    reminders = BillReminderSerializer(many=True, read_only=True)
    days_until_due = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Bill
        fields = ['id', 'vendor', 'vendor_name', 'bill_no', 'bill_date', 'due_date', 
                 'amount', 'currency', 'currency_code', 'currency_symbol', 'currency_name', 
                 'status', 'confirmed', 'notes', 'created_by', 'created_by_name',
                 'created_at', 'updated_at', 'history', 'reminders', 'days_until_due', 'is_overdue']
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at', 'updated_at', 
                           'history', 'reminders', 'days_until_due', 'is_overdue']

    def get_days_until_due(self, obj):
        """Calculate days until due date"""
        from django.utils import timezone
        if obj.due_date:
            delta = obj.due_date - timezone.now().date()
            return delta.days
        return None

    def get_is_overdue(self, obj):
        """Check if bill is overdue"""
        days_until_due = self.get_days_until_due(obj)
        return days_until_due is not None and days_until_due < 0 and obj.status != 'paid'

    def validate_bill_no(self, value):
        """Validate bill number uniqueness"""
        if self.instance:
            # Update case - exclude current instance
            if Bill.objects.exclude(pk=self.instance.pk).filter(bill_no=value).exists():
                raise serializers.ValidationError("Bill number already exists.")
        else:
            # Create case
            if Bill.objects.filter(bill_no=value).exists():
                raise serializers.ValidationError("Bill number already exists.")
        return value

    def validate_due_date(self, value):
        """Validate due date is not in the past"""
        from django.utils import timezone
        if value and value < timezone.now().date():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value

    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, data):
        """Cross-field validation"""
        if 'bill_date' in data and 'due_date' in data:
            if data['due_date'] < data['bill_date']:
                raise serializers.ValidationError({
                    'due_date': 'Due date cannot be earlier than bill date.'
                })
        return data


class BillCreateSerializer(BillSerializer):
    """Serializer for creating bills with minimal fields"""
    
    class Meta(BillSerializer.Meta):
        fields = ['id', 'vendor', 'bill_no', 'bill_date', 'due_date', 'amount', 'status', 'notes']
        read_only_fields = ['id']


class BillUpdateSerializer(BillSerializer):
    """Serializer for updating bills"""
    
    class Meta(BillSerializer.Meta):
        fields = ['vendor', 'bill_no', 'bill_date', 'due_date', 'amount', 'notes', 'confirmed']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class BillActionSerializer(serializers.Serializer):
    """Serializer for bill actions (mark paid, confirm)"""
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_notes(self, value):
        """Validate notes length"""
        if value and len(value.strip()) == 0:
            return None
        return value


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    today_due_count = serializers.IntegerField()
    today_due_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    overdue_count = serializers.IntegerField()
    overdue_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    upcoming_count = serializers.IntegerField()
    upcoming_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pending_count = serializers.IntegerField()
    total_pending_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    paid_this_month_count = serializers.IntegerField()
    paid_this_month_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    default_currency_code = serializers.CharField(required=False)
    default_currency_symbol = serializers.CharField(required=False)
    default_currency_name = serializers.CharField(required=False)


class BillFilterSerializer(serializers.Serializer):
    """Serializer for bill filtering parameters"""
    status = serializers.ChoiceField(
        choices=[('pending', 'Pending'), ('paid', 'Paid'), ('overdue', 'Overdue')],
        required=False
    )
    vendor = serializers.IntegerField(required=False)
    search = serializers.CharField(max_length=100, required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    confirmed = serializers.BooleanField(required=False)
    amount_min = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    amount_max = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    
    def validate(self, data):
        """Cross-field validation for filters"""
        if 'date_from' in data and 'date_to' in data:
            if data['date_to'] < data['date_from']:
                raise serializers.ValidationError({
                    'date_to': 'End date cannot be earlier than start date.'
                })
        
        if 'amount_min' in data and 'amount_max' in data:
            if data['amount_max'] < data['amount_min']:
                raise serializers.ValidationError({
                    'amount_max': 'Maximum amount cannot be less than minimum amount.'
                })
        
        return data