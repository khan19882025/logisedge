import React, { useState, useEffect } from 'react';
import axios from 'axios';

const PaymentSourceForm = ({ paymentSource, onSubmit, onCancel, isEdit = false }) => {
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        payment_type: '',
        linked_account: '',
        is_active: true
    });
    
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({});
    const [suggestedAccount, setSuggestedAccount] = useState(null);
    
    const paymentTypeChoices = [
        { value: 'prepaid', label: 'Prepaid' },
        { value: 'postpaid', label: 'Postpaid' },
        { value: 'cash_bank', label: 'Cash/Bank' }
    ];
    
    useEffect(() => {
        // Load accounts for dropdown
        loadAccounts();
        
        // If editing, populate form with existing data
        if (paymentSource && isEdit) {
            setFormData({
                name: paymentSource.name || '',
                description: paymentSource.description || '',
                payment_type: paymentSource.payment_type || '',
                linked_account: paymentSource.linked_account?.id || '',
                is_active: paymentSource.is_active !== undefined ? paymentSource.is_active : true
            });
        }
    }, [paymentSource, isEdit]);
    
    useEffect(() => {
        // When payment type changes, suggest appropriate account
        if (formData.payment_type) {
            suggestLinkedAccount(formData.payment_type);
        }
    }, [formData.payment_type]);
    
    const loadAccounts = async () => {
        try {
            setLoading(true);
            const response = await axios.get('/api/accounts/', {
                params: { is_active: true }
            });
            setAccounts(response.data.results || response.data);
        } catch (error) {
            console.error('Error loading accounts:', error);
        } finally {
            setLoading(false);
        }
    };
    
    const suggestLinkedAccount = (paymentType) => {
        if (!accounts.length) return;
        
        let suggestedAccount = null;
        
        if (paymentType === 'prepaid') {
            // Look for asset accounts (prepaid deposits)
            suggestedAccount = accounts.find(account => 
                account.account_type?.category === 'ASSET' &&
                (account.name.toLowerCase().includes('prepaid') || 
                 account.name.toLowerCase().includes('deposit'))
            );
        } else if (paymentType === 'postpaid') {
            // Look for liability accounts (payables)
            suggestedAccount = accounts.find(account => 
                account.account_type?.category === 'LIABILITY' &&
                (account.name.toLowerCase().includes('payable') || 
                 account.name.toLowerCase().includes('liability'))
            );
        } else if (paymentType === 'cash_bank') {
            // Look for asset accounts (bank/cash)
            suggestedAccount = accounts.find(account => 
                account.account_type?.category === 'ASSET' &&
                (account.name.toLowerCase().includes('bank') || 
                 account.name.toLowerCase().includes('cash') ||
                 account.name.toLowerCase().includes('current'))
            );
        }
        
        setSuggestedAccount(suggestedAccount);
        
        // Auto-select suggested account if no account is currently selected
        if (suggestedAccount && !formData.linked_account) {
            setFormData(prev => ({
                ...prev,
                linked_account: suggestedAccount.id
            }));
        }
    };
    
    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
        
        // Clear errors when user starts typing
        if (errors[name]) {
            setErrors(prev => ({
                ...prev,
                [name]: ''
            }));
        }
    };
    
    const validateForm = () => {
        const newErrors = {};
        
        if (!formData.name.trim()) {
            newErrors.name = 'Payment source name is required';
        }
        
        if (!formData.payment_type) {
            newErrors.payment_type = 'Payment type is required';
        }
        
        if (!formData.linked_account) {
            newErrors.linked_account = 'Linked account is required';
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }
        
        try {
            setLoading(true);
            
            if (isEdit) {
                await axios.put(`/api/payment-sources/${paymentSource.id}/`, formData);
            } else {
                await axios.post('/api/payment-sources/', formData);
            }
            
            onSubmit();
        } catch (error) {
            console.error('Error saving payment source:', error);
            
            if (error.response?.data?.errors) {
                setErrors(error.response.data.errors);
            } else {
                setErrors({ general: 'An error occurred while saving the payment source' });
            }
        } finally {
            setLoading(false);
        }
    };
    
    const getAccountDisplayName = (accountId) => {
        const account = accounts.find(acc => acc.id === accountId);
        return account ? `${account.account_code} - ${account.name}` : '';
    };
    
    return (
        <div className="card">
            <div className="card-header">
                <h5 className="card-title mb-0">
                    {isEdit ? 'Edit Payment Source' : 'Create New Payment Source'}
                </h5>
            </div>
            <div className="card-body">
                <form onSubmit={handleSubmit}>
                    {errors.general && (
                        <div className="alert alert-danger" role="alert">
                            {errors.general}
                        </div>
                    )}
                    
                    <div className="row">
                        <div className="col-md-6">
                            <div className="mb-3">
                                <label htmlFor="name" className="form-label">
                                    Payment Source Name <span className="text-danger">*</span>
                                </label>
                                <input
                                    type="text"
                                    className={`form-control ${errors.name ? 'is-invalid' : ''}`}
                                    id="name"
                                    name="name"
                                    value={formData.name}
                                    onChange={handleInputChange}
                                    placeholder="Enter payment source name"
                                    maxLength={50}
                                    required
                                />
                                {errors.name && (
                                    <div className="invalid-feedback">{errors.name}</div>
                                )}
                            </div>
                        </div>
                        
                        <div className="col-md-6">
                            <div className="mb-3">
                                <label htmlFor="payment_type" className="form-label">
                                    Payment Type <span className="text-danger">*</span>
                                </label>
                                <select
                                    className={`form-control ${errors.payment_type ? 'is-invalid' : ''}`}
                                    id="payment_type"
                                    name="payment_type"
                                    value={formData.payment_type}
                                    onChange={handleInputChange}
                                    required
                                >
                                    <option value="">Select payment type</option>
                                    {paymentTypeChoices.map(choice => (
                                        <option key={choice.value} value={choice.value}>
                                            {choice.label}
                                        </option>
                                    ))}
                                </select>
                                {errors.payment_type && (
                                    <div className="invalid-feedback">{errors.payment_type}</div>
                                )}
                            </div>
                        </div>
                    </div>
                    
                    <div className="mb-3">
                        <label htmlFor="linked_account" className="form-label">
                            Linked Account <span className="text-danger">*</span>
                        </label>
                        <select
                            className={`form-control ${errors.linked_account ? 'is-invalid' : ''}`}
                            id="linked_account"
                            name="linked_account"
                            value={formData.linked_account}
                            onChange={handleInputChange}
                            required
                        >
                            <option value="">Select an account</option>
                            {accounts.map(account => (
                                <option key={account.id} value={account.id}>
                                    {account.account_code} - {account.name} ({account.account_type?.category})
                                </option>
                            ))}
                        </select>
                        {errors.linked_account && (
                            <div className="invalid-feedback">{errors.linked_account}</div>
                        )}
                        
                        {suggestedAccount && suggestedAccount.id !== formData.linked_account && (
                            <div className="form-text text-info">
                                💡 Suggested account: {suggestedAccount.account_code} - {suggestedAccount.name}
                                <button
                                    type="button"
                                    className="btn btn-sm btn-outline-info ms-2"
                                    onClick={() => setFormData(prev => ({
                                        ...prev,
                                        linked_account: suggestedAccount.id
                                    }))}
                                >
                                    Use This
                                </button>
                            </div>
                        )}
                    </div>
                    
                    <div className="mb-3">
                        <label htmlFor="description" className="form-label">Description</label>
                        <textarea
                            className="form-control"
                            id="description"
                            name="description"
                            value={formData.description}
                            onChange={handleInputChange}
                            rows={4}
                            placeholder="Enter optional description"
                        />
                    </div>
                    
                    <div className="mb-3">
                        <div className="form-check">
                            <input
                                className="form-check-input"
                                type="checkbox"
                                id="is_active"
                                name="is_active"
                                checked={formData.is_active}
                                onChange={handleInputChange}
                            />
                            <label className="form-check-label" htmlFor="is_active">
                                Active
                            </label>
                        </div>
                    </div>
                    
                    <div className="d-flex justify-content-end gap-2">
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={onCancel}
                            disabled={loading}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                    Saving...
                                </>
                            ) : (
                                isEdit ? 'Update' : 'Create'
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default PaymentSourceForm;
