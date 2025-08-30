from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Item(models.Model):
    """Item model for managing inventory items"""
    
    ITEM_CATEGORIES = [
        # Food & Beverages
        ('toiletries', 'Toiletries'),
        ('food_beverages', 'Food & Beverages'),
        ('dairy_products', 'Dairy Products'),
        ('frozen_food', 'Frozen Food'),
        ('bakery_items', 'Bakery Items'),
        ('snacks', 'Snacks'),
        ('meat_seafood', 'Meat & Seafood'),
        ('fruits_vegetables', 'Fruits & Vegetables'),
        ('spices_condiments', 'Spices & Condiments'),
        ('cooking_essentials', 'Cooking Essentials'),
        
        # Automobile
        ('automobile', 'Automobile'),
        ('car_accessories', 'Car Accessories'),
        ('bike_accessories', 'Bike Accessories'),
        ('tyres_tubes', 'Tyres & Tubes'),
        ('lubricants', 'Lubricants'),
        
        # Electronics
        ('electronics', 'Electronics'),
        ('mobile_phones', 'Mobile Phones'),
        ('televisions', 'Televisions'),
        ('cameras', 'Cameras'),
        ('audio_devices', 'Audio Devices'),
        ('computers_parts', 'Computers & Parts'),
        ('laptops', 'Laptops'),
        ('desktops', 'Desktops'),
        ('keyboards_mice', 'Keyboards & Mice'),
        ('monitors', 'Monitors'),
        ('storage_devices', 'Storage Devices'),
        ('printers_scanners', 'Printers & Scanners'),
        
        # Household Items
        ('household_items', 'Household Items'),
        ('furniture', 'Furniture'),
        ('lighting', 'Lighting'),
        ('kitchenware', 'Kitchenware'),
        ('storage_containers', 'Storage & Containers'),
        ('cleaning_supplies', 'Cleaning Supplies'),
        ('kitchen_appliances', 'Kitchen Appliances'),
        ('home_decor', 'Home Decor'),
        ('curtains_carpets', 'Curtains & Carpets'),
        
        # Office Supplies
        ('office_supplies', 'Office Supplies'),
        ('stationery', 'Stationery'),
        ('paper_products', 'Paper Products'),
        ('files_folders', 'Files & Folders'),
        
        # Beauty & Personal Care
        ('beauty_personal_care', 'Beauty & Personal Care'),
        ('skin_care', 'Skin Care'),
        ('hair_care', 'Hair Care'),
        ('oral_care', 'Oral Care'),
        ('perfumes_deodorants', 'Perfumes & Deodorants'),
        
        # Health & Wellness
        ('health_wellness', 'Health & Wellness'),
        ('medicines', 'Medicines'),
        ('first_aid', 'First Aid'),
        ('supplements', 'Supplements'),
        ('fitness_equipment', 'Fitness Equipment'),
        
        # Baby Products
        ('baby_products', 'Baby Products'),
        ('diapers', 'Diapers'),
        ('baby_food', 'Baby Food'),
        ('baby_toiletries', 'Baby Toiletries'),
        ('toys_games', 'Toys & Games'),
        
        # Clothing & Apparel
        ('clothing_apparel', 'Clothing & Apparel'),
        ('mens_clothing', "Men's Clothing"),
        ('womens_clothing', "Women's Clothing"),
        ('kids_clothing', "Kids' Clothing"),
        ('footwear', 'Footwear'),
        ('bags_luggage', 'Bags & Luggage'),
        
        # Sports & Outdoor
        ('sports_outdoor', 'Sports & Outdoor'),
        ('garden_supplies', 'Garden Supplies'),
        ('pet_supplies', 'Pet Supplies'),
        ('books_magazines', 'Books & Magazines'),
        
        # Construction Materials
        ('construction_materials', 'Construction Materials'),
        ('electrical_supplies', 'Electrical Supplies'),
        ('plumbing_materials', 'Plumbing Materials'),
        ('tools_hardware', 'Tools & Hardware'),
        ('paint_accessories', 'Paint & Accessories'),
        ('safety_equipment', 'Safety Equipment'),
        ('packaging_materials', 'Packaging Materials'),
        ('travel_accessories', 'Travel Accessories'),
        ('party_supplies', 'Party Supplies'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
    ]
    
    # Basic Information
    item_code = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9-]+$', 'Item code must contain only uppercase letters, numbers, and hyphens.')],
        help_text="Unique item code (e.g., ITM-001, PROD-002)"
    )
    item_name = models.CharField(max_length=200, help_text="Full name of the item")
    item_category = models.CharField(max_length=50, choices=ITEM_CATEGORIES, default='household_items')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Description and Details
    description = models.TextField(blank=True, help_text="Detailed description of the item")
    short_description = models.CharField(max_length=500, blank=True, help_text="Brief description for display")
    
    # Specifications
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=50, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, help_text="Weight in kg")
    color = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=100, blank=True)
    
    # Inventory Information
    unit_of_measure = models.CharField(max_length=20, default='PCS', help_text="Unit of measurement (PCS, KG, L, etc.)")
    min_stock_level = models.PositiveIntegerField(default=0, help_text="Minimum stock level for reorder")
    max_stock_level = models.PositiveIntegerField(default=0, help_text="Maximum stock level")
    reorder_point = models.PositiveIntegerField(default=0, help_text="Stock level at which to reorder")
    
    # Pricing Information
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Cost price per unit")
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Selling price per unit")
    currency = models.CharField(max_length=3, default='USD')
    
    # Supplier Information
    supplier = models.CharField(max_length=200, blank=True, help_text="Primary supplier name")
    supplier_code = models.CharField(max_length=50, blank=True, help_text="Supplier's item code")
    lead_time = models.PositiveIntegerField(default=0, help_text="Lead time in days")
    
    # Location and Storage
    warehouse_location = models.CharField(max_length=100, blank=True, help_text="Storage location in warehouse")
    shelf_number = models.CharField(max_length=20, blank=True)
    bin_number = models.CharField(max_length=20, blank=True)
    
    # Additional Information
    barcode = models.CharField(max_length=50, blank=True, unique=True, help_text="Barcode or SKU")
    serial_number = models.CharField(max_length=100, blank=True, help_text="Serial number if applicable")
    warranty_period = models.PositiveIntegerField(default=0, help_text="Warranty period in months")
    
    # Notes and Metadata
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal notes not visible to customers")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='items_created'
    )
    updated_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='items_updated'
    )
    
    # New fields
    hs_code = models.CharField(max_length=32, blank=True, null=True, help_text="HS Code")
    country_of_origin = models.CharField(max_length=64, blank=True, null=True, help_text="Country of Origin")
    cbm = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, help_text="Cubic Meter (CBM)")
    net_weight = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, help_text="Net Weight (kg)")
    gross_weight = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, help_text="Gross Weight (kg)")
    
    class Meta:
        ordering = ['item_name']
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        db_table = 'item'
    
    def __str__(self):
        return f"{self.item_code} - {self.item_name}"
    
    @property
    def is_active(self):
        """Check if item is active"""
        return self.status == 'active'
    
    @property
    def display_name(self):
        """Return display name with code"""
        return f"{self.item_code} - {self.item_name}"
    
    @property
    def profit_margin(self):
        """Calculate profit margin if both prices are available"""
        if self.cost_price and self.selling_price and self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return 0
    
    @property
    def profit_amount(self):
        """Calculate profit amount per unit"""
        if self.cost_price and self.selling_price:
            return self.selling_price - self.cost_price
        return 0
    
    def get_full_specifications(self):
        """Return full specifications as a dictionary"""
        specs = {}
        if self.brand:
            specs['Brand'] = self.brand
        if self.model:
            specs['Model'] = self.model
        if self.size:
            specs['Size'] = self.size
        if self.weight:
            specs['Weight'] = f"{self.weight} kg"
        if self.color:
            specs['Color'] = self.color
        if self.material:
            specs['Material'] = self.material
        return specs
