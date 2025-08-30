# How to Add New Payment Sources

## Overview
Instead of deleting existing payment sources (Bank Transfer, Cash, Cheque, Credit Card), you can add new ones using the enhanced form with professional fields.

## Access the Payment Source Creation Form

### Option 1: Direct URL Access
Navigate to: `/payment-source/create/` in your browser

### Option 2: From Payment Source List
1. Go to `/payment-source/` (Payment Sources list)
2. Click the "Add Payment Source" button

## New Payment Source Form Fields

### 1. Basic Information
- **Name** (Required): Unique name for the payment source
- **Short Code** (Optional): Unique short identifier (max 20 characters)
- **Description** (Optional): Detailed description

### 2. Classification
- **Payment Type** (Required): 
  - Prepaid
  - Postpaid
  - Cash/Bank
- **Source Type** (Required): 
  - Prepaid
  - Postpaid
- **Category** (Required):
  - Cash
  - Bank
  - Credit Card
  - Advance Account
  - Other Payable

### 3. Financial Settings
- **Currency** (Optional): Select from available currencies (defaults to AED)
- **Linked Ledger** (Required): Chart of Account linked to this payment source
- **Default Expense Ledger** (Optional): Default expense account

### 4. Vendor Settings
- **Default Vendor** (Optional): Default vendor for this payment source

### 5. Status and Remarks
- **Active**: Enable/disable the payment source
- **Remarks** (Optional): Additional notes

## Example: Adding a New Payment Source

### Scenario: Adding "Digital Wallet" Payment Source

1. **Basic Information**
   - Name: `Digital Wallet`
   - Code: `DW001`
   - Description: `Digital wallet payments including Apple Pay, Google Pay, and Samsung Pay`

2. **Classification**
   - Payment Type: `Postpaid`
   - Source Type: `Postpaid`
   - Category: `Other Payable`

3. **Financial Settings**
   - Currency: `AED` (or select appropriate currency)
   - Linked Ledger: Select appropriate Chart of Account (e.g., "Digital Payments")
   - Default Expense Ledger: Leave empty or select appropriate expense account

4. **Vendor Settings**
   - Default Vendor: Leave empty or select appropriate vendor

5. **Status and Remarks**
   - Active: ✓ (checked)
   - Remarks: `Modern digital payment method for tech-savvy customers`

## Example: Adding "Corporate Credit Card" Payment Source

1. **Basic Information**
   - Name: `Corporate Credit Card`
   - Code: `CCC001`
   - Description: `Corporate credit card payments for business expenses`

2. **Classification**
   - Payment Type: `Postpaid`
   - Source Type: `Postpaid`
   - Category: `Credit Card`

3. **Financial Settings**
   - Currency: `AED`
   - Linked Ledger: Select "Corporate Credit Card" account
   - Default Expense Ledger: Select "Business Expenses" account

4. **Vendor Settings**
   - Default Vendor: Leave empty

5. **Status and Remarks**
   - Active: ✓ (checked)
   - Remarks: `For corporate business expenses and travel`

## Example: Adding "Advance Payment" Payment Source

1. **Basic Information**
   - Name: `Advance Payment`
   - Code: `AP001`
   - Description: `Advance payments received before service delivery`

2. **Classification**
   - Payment Type: `Prepaid`
   - Source Type: `Prepaid`
   - Category: `Advance Account`

3. **Financial Settings**
   - Currency: `AED`
   - Linked Ledger: Select "Advance Payments" account
   - Default Expense Ledger: Leave empty

4. **Vendor Settings**
   - Default Vendor: Leave empty

5. **Status and Remarks**
   - Active: ✓ (checked)
   - Remarks: `For advance payments and deposits`

## Benefits of the New System

### 1. Better Organization
- Clear categorization of payment sources
- Professional field structure
- Better search and filtering

### 2. Enhanced Functionality
- Multi-currency support
- Linked to Chart of Accounts
- Default expense and vendor settings
- Comprehensive remarks and notes

### 3. Improved Reporting
- Better financial analysis
- Enhanced tracking capabilities
- Professional audit trail

## Tips for Adding Payment Sources

### 1. Naming Convention
- Use descriptive names
- Include business context
- Be consistent with existing naming

### 2. Code Assignment
- Use meaningful codes
- Include department/type prefixes
- Keep codes short but descriptive

### 3. Category Selection
- Choose the most appropriate category
- Consider future reporting needs
- Align with business processes

### 4. Linked Ledger
- Select the most appropriate Chart of Account
- Consider the financial impact
- Ensure proper accounting treatment

## Access URLs

- **List View**: `/payment-source/`
- **Create New**: `/payment-source/create/`
- **View Details**: `/payment-source/{id}/`
- **Edit**: `/payment-source/{id}/edit/`

## Need Help?

If you encounter any issues or need assistance:
1. Check the form validation messages
2. Ensure all required fields are filled
3. Verify the linked ledger exists in Chart of Accounts
4. Check that the currency is active

The new system provides a much more professional and organized way to manage payment sources while preserving all your existing data.
