import React, { useState } from 'react';
import PaymentSourceList from './PaymentSourceList';
import PaymentSourceForm from './PaymentSourceForm';

const PaymentSourceManager = () => {
    const [currentView, setCurrentView] = useState('list'); // 'list' or 'form'
    const [editingPaymentSource, setEditingPaymentSource] = useState(null);
    
    const handleCreate = () => {
        setEditingPaymentSource(null);
        setCurrentView('form');
    };
    
    const handleEdit = (paymentSource) => {
        setEditingPaymentSource(paymentSource);
        setCurrentView('form');
    };
    
    const handleFormSubmit = () => {
        setCurrentView('list');
        setEditingPaymentSource(null);
    };
    
    const handleFormCancel = () => {
        setCurrentView('list');
        setEditingPaymentSource(null);
    };
    
    const handleBackToList = () => {
        setCurrentView('list');
        setEditingPaymentSource(null);
    };
    
    if (currentView === 'form') {
        return (
            <div>
                <div className="mb-3">
                    <button
                        className="btn btn-outline-secondary"
                        onClick={handleBackToList}
                    >
                        <i className="fas fa-arrow-left me-2"></i>
                        Back to Payment Sources
                    </button>
                </div>
                
                <PaymentSourceForm
                    paymentSource={editingPaymentSource}
                    onSubmit={handleFormSubmit}
                    onCancel={handleFormCancel}
                    isEdit={!!editingPaymentSource}
                />
            </div>
        );
    }
    
    return (
        <PaymentSourceList
            onCreate={handleCreate}
            onEdit={handleEdit}
        />
    );
};

export default PaymentSourceManager;
