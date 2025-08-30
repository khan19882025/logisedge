# RF Scanner App

A mobile and tablet-compatible warehouse management system for barcode scanning operations.

## Features

### Core Operations
- **Inbound**: Receive and putaway operations
- **Outbound**: Pick and ship operations  
- **Location Change**: Move items between locations
- **Physical Check**: Inventory counting and verification

### Key Features
- Mobile and tablet responsive design
- Real-time scanning interface
- Session-based operations
- Barcode scanning with auto-focus
- Location and item management
- Scan history and reporting
- API endpoints for mobile apps

## Access

- **URL**: `/rf-scanner/`
- **Login**: `/rf-scanner/login/`
- **Dashboard**: `/rf-scanner/`

## Setup

1. **Install the app**:
   ```bash
   python manage.py makemigrations rf_scanner
   python manage.py migrate
   ```

2. **Create sample data**:
   ```bash
   python manage.py setup_rf_data
   ```

3. **Create RF User**:
   - Go to Django Admin
   - Create an RFUser profile for warehouse operators
   - Link to existing Django User accounts

## Usage

### For Warehouse Operators

1. **Login** with Employee ID, Username, and Password
2. **Select Operation** from dashboard:
   - Inbound (Receive & Putaway)
   - Outbound (Pick & Ship)
   - Location Change (Move Items)
   - Physical Check (Inventory Count)
3. **Start Session** and begin scanning
4. **Scan barcodes** using the scanning interface
5. **End Session** when complete

### For Administrators

- **Manage Users**: Create RFUser profiles in Django Admin
- **Manage Items**: Add/update items with barcodes
- **Manage Locations**: Set up warehouse locations
- **View Reports**: Monitor scan history and sessions

## API Endpoints

### Scan API
- **POST** `/rf-scanner/api/scan/`
- **Body**: `{"barcode": "123456", "session_id": 1, "quantity": 1, "location": "A1-01"}`

## Mobile Optimization

The app is optimized for:
- **Mobile phones**: Touch-friendly interface
- **Tablets**: Larger screen layouts
- **Barcode scanners**: Auto-focus and keyboard events
- **Offline capability**: Session-based operations

## Security

- Separate login system for RF Scanner
- Employee ID verification
- Session-based authentication
- User activity tracking

## Models

- **RFUser**: Warehouse operator profiles
- **ScanSession**: Operation sessions
- **ScanRecord**: Individual scan records
- **Location**: Warehouse locations
- **Item**: Inventory items with barcodes 