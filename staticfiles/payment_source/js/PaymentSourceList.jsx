import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PaymentSourceForm from './PaymentSourceForm';

const PaymentSourceList = () => {
    const [paymentSources, setPaymentSources] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingPaymentSource, setEditingPaymentSource] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [paymentTypeFilter, setPaymentTypeFilter] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    
    const paymentTypeChoices = [
        { value: 'prepaid', label: 'Prepaid' },
        { value: 'postpaid', label: 'Postpaid' },
        { value: 'cash_bank', label: 'Cash/Bank' }
    ];
    
    useEffect(() => {
        loadPaymentSources();
    }, [searchTerm, paymentTypeFilter, statusFilter]);
    
    const loadPaymentSources = async () => {
        try {
            setLoading(true);
            const params = {};
            
            if (searchTerm) params.search = searchTerm;
            if (paymentTypeFilter) params.payment_type = paymentTypeFilter;
            if (statusFilter) params.is_active = statusFilter === 'active';
            
            const response = await axios.get('/api/payment-sources/', { params });
            setPaymentSources(response.data.results || response.data);
        } catch (error) {
            console.error('Error loading payment sources:', error);
        } finally {
            setLoading(false);
        }
    };
    
    const handleCreate = () => {
        setEditingPaymentSource(null);
        setShowForm(true);
    };
    
    const handleEdit = (paymentSource) => {
        setEditingPaymentSource(paymentSource);
        setShowForm(true);
    };
    
    const handleDelete = async (paymentSource) => {
        if (!window.confirm(`Are you sure you want to deactivate "${paymentSource.name}"?`)) {
            return;
        }
        
        try {
            await axios.delete(`/api/payment-sources/${paymentSource.id}/`);
            loadPaymentSources();
        } catch (error) {
            console.error('Error deleting payment source:', error);
            alert('Error deleting payment source');
        }
    };
    
    const handleRestore = async (paymentSource) => {
        try {
            await axios.patch(`/api/payment-sources/${paymentSource.id}/`, {
                is_active: true
            });
            loadPaymentSources();
        } catch (error) {
            console.error('Error restoring payment source:', error);
            alert('Error restoring payment source');
        }
    };
    
    const handleFormSubmit = () => {
        setShowForm(false);
        setEditingPaymentSource(null);
        loadPaymentSources();
    };
    
    const handleFormCancel = () => {
        setShowForm(false);
        setEditingPaymentSource(null);
    };
    
    const getStatusBadge = (isActive) => {
        return isActive ? (
            <span className="badge bg-success">Active</span>
        ) : (
            <span className="badge bg-secondary">Inactive</span>
        );
    };
    
    const getPaymentTypeBadge = (paymentType) => {
        const typeMap = {
            prepaid: { class: 'bg-info', label: 'Prepaid' },
            postpaid: { class: 'bg-warning', label: 'Postpaid' },
            cash_bank: { class: 'bg-primary', label: 'Cash/Bank' }
        };
        
        const type = typeMap[paymentType] || { class: 'bg-secondary', label: 'Unknown' };
        return <span className={`badge ${type.class}`}>{type.label}</span>;
    };
    
    if (showForm) {
        return (
            <PaymentSourceForm
                paymentSource={editingPaymentSource}
                onSubmit={handleFormSubmit}
                onCancel={handleFormCancel}
                isEdit={!!editingPaymentSource}
            />
        );
    }
    
    return (
        <div className="card">
            <div className="card-header">
                <div className="d-flex justify-content-between align-items-center">
                    <h5 className="card-title mb-0">Payment Sources</h5>
                    <button
                        className="btn btn-primary"
                        onClick={handleCreate}
                    >
                        <i className="fas fa-plus me-2"></i>
                        Create Payment Source
                    </button>
                </div>
            </div>
            
            <div className="card-body">
                {/* Search and Filters */}
                <div className="row mb-3">
                    <div className="col-md-4">
                        <input
                            type="text"
                            className="form-control"
                            placeholder="Search payment sources..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div className="col-md-3">
                        <select
                            className="form-control"
                            value={paymentTypeFilter}
                            onChange={(e) => setPaymentTypeFilter(e.target.value)}
                        >
                            <option value="">All Payment Types</option>
                            {paymentTypeChoices.map(choice => (
                                <option key={choice.value} value={choice.value}>
                                    {choice.label}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="col-md-3">
                        <select
                            className="form-control"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                        >
                            <option value="">All Status</option>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                        </select>
                    </div>
                    <div className="col-md-2">
                        <button
                            className="btn btn-outline-secondary w-100"
                            onClick={loadPaymentSources}
                        >
                            <i className="fas fa-search"></i>
                        </button>
                    </div>
                </div>
                
                {/* Payment Sources Table */}
                {loading ? (
                    <div className="text-center py-4">
                        <div className="spinner-border" role="status">
                            <span className="visually-hidden">Loading...</span>
                        </div>
                    </div>
                ) : paymentSources.length === 0 ? (
                    <div className="text-center py-4">
                        <p className="text-muted">No payment sources found</p>
                        <button
                            className="btn btn-primary"
                            onClick={handleCreate}
                        >
                            Create your first payment source
                        </button>
                    </div>
                ) : (
                    <div className="table-responsive">
                        <table className="table table-hover">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Payment Type</th>
                                    <th>Linked Account</th>
                                    <th>Description</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {paymentSources.map(paymentSource => (
                                    <tr key={paymentSource.id}>
                                        <td>
                                            <strong>{paymentSource.name}</strong>
                                        </td>
                                        <td>
                                            {getPaymentTypeBadge(paymentSource.payment_type)}
                                        </td>
                                        <td>
                                            {paymentSource.linked_account_display || 'Not linked'}
                                        </td>
                                        <td>
                                            {paymentSource.description ? (
                                                <span className="text-muted">
                                                    {paymentSource.description.length > 50
                                                        ? `${paymentSource.description.substring(0, 50)}...`
                                                        : paymentSource.description
                                                    }
                                                </span>
                                            ) : (
                                                <span className="text-muted">No description</span>
                                            )}
                                        </td>
                                        <td>
                                            {getStatusBadge(paymentSource.is_active)}
                                        </td>
                                        <td>
                                            <div className="btn-group btn-group-sm" role="group">
                                                <button
                                                    className="btn btn-outline-primary"
                                                    onClick={() => handleEdit(paymentSource)}
                                                    title="Edit"
                                                >
                                                    <i className="fas fa-edit"></i>
                                                </button>
                                                
                                                {paymentSource.is_active ? (
                                                    <button
                                                        className="btn btn-outline-danger"
                                                        onClick={() => handleDelete(paymentSource)}
                                                        title="Deactivate"
                                                    >
                                                        <i className="fas fa-trash"></i>
                                                    </button>
                                                ) : (
                                                    <button
                                                        className="btn btn-outline-success"
                                                        onClick={() => handleRestore(paymentSource)}
                                                        title="Restore"
                                                    >
                                                        <i className="fas fa-undo"></i>
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PaymentSourceList;
