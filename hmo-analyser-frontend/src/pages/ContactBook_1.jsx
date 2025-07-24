import React, { useState, useEffect } from 'react';
import { Search, Plus, Edit2, Trash2, Phone, Mail, MapPin, Building, User, Download, Upload, Star, Calendar, MessageSquare, AlertCircle, Loader2, Wifi, WifiOff, X } from 'lucide-react';
import { contactsAPI, migrateFromLocalStorage } from '../utils/contactsApi';
import UserMenu from '../components/UserMenu'
import { useAuth} from '../components/AuthContext'

const ContactBook_1 = () => {
  const { user } =useAuth();
    const [contacts, setContacts] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedContact, setSelectedContact] = useState(null);
    const [showForm, setShowForm] = useState(false);
    const [editingContact, setEditingContact] = useState(null);
    const [filterCategory, setFilterCategory] = useState('all');
    const [viewMode, setViewMode] = useState('grid');
    const [favorites, setFavorites] = useState(new Set());

    // Loading and error states
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [apiConnected, setApiConnected] = useState(false);
    const [showMigration, setShowMigration] = useState(false);
    // Add these after the existing state variables
        const [contactLists, setContactLists] = useState([]);
        const [selectedListId, setSelectedListId] = useState(null);
        const [showListForm, setShowListForm] = useState(false);

    // Check API connectivity and load data
    useEffect(() => {
        initializeContactBook();
    }, []);

    const initializeContactBook = async () => {
        try {
        setLoading(true);
        setError(null);

        // Check if API is available
        const isApiHealthy = await contactsAPI.healthCheck();
        setApiConnected(isApiHealthy);

        if (!isApiHealthy) {
            throw new Error('Cannot connect to the contact book API. Please ensure the backend server is running.');
        }

        // Load contacts and favorites
            await Promise.all([
                loadContactLists(),
                loadFavorites()
                ]);

        // Check if we need to offer migration from localStorage
        checkForMigration();

        } catch (err) {
        console.error('Failed to initialize contact book:', err);
        setError(err.message);
        } finally {
        setLoading(false);
        }
    };

    const loadContactLists = async () => {
        try {
            const lists = await contactsAPI.getContactLists();
            setContactLists(lists);
            
            // Set default list if no list is selected
            if (!selectedListId && lists.length > 0) {
            const defaultList = lists.find(list => list.is_default) || lists[0];
            setSelectedListId(defaultList.id);
            }
        } catch (err) {
            console.error('Failed to load contact lists:', err);
            throw new Error('Failed to load contact lists from server');
        }
    };

    const loadContacts = async (filters = {}) => {
        try {
        const allContacts = await contactsAPI.getAllContacts({
            search: searchTerm || undefined,
            category: filterCategory !== 'all' ? filterCategory : undefined,
            contact_list_id: selectedListId || undefined, // Add this line
            ...filters
        });
        setContacts(allContacts);
        } catch (err) {
        console.error('Failed to load contacts:', err);
        throw new Error('Failed to load contacts from server');
        }
    };

    const loadFavorites = async () => {
        try {
        const favoriteIds = await contactsAPI.getFavorites();
        setFavorites(new Set(favoriteIds));
        } catch (err) {
        console.error('Failed to load favorites:', err);
        // Don't throw - favorites are not critical
        }
    };

    const checkForMigration = () => {
        const localContacts = localStorage.getItem('hmo-contacts');
        if (localContacts && JSON.parse(localContacts).length > 0) {
        setShowMigration(true);
        }
    };

    // Refresh data when search or filter changes
    useEffect(() => {
    if (apiConnected && !loading && selectedListId) {
        loadContacts();
    }
    }, [searchTerm, filterCategory, selectedListId]);

    const categories = [
        { value: 'all', label: '👥 All Contacts', count: contacts.length },
        { value: 'landlord', label: '🏠 Landlords', count: contacts.filter(c => c.category === 'landlord').length },
        { value: 'tenant', label: '👤 Tenants', count: contacts.filter(c => c.category === 'tenant').length },
        { value: 'contractor', label: '🔧 Contractors', count: contacts.filter(c => c.category === 'contractor').length },
        { value: 'agent', label: '🏢 Agents', count: contacts.filter(c => c.category === 'agent').length },
        { value: 'supplier', label: '📦 Suppliers', count: contacts.filter(c => c.category === 'supplier').length },
        { value: 'other', label: '📋 Other', count: contacts.filter(c => c.category === 'other').length }
    ];

    const addContact = async (contactData) => {
    try {
        setLoading(true);
        const newContact = await contactsAPI.createContact({
        ...contactData,
        contact_list_id: selectedListId
        });
        await Promise.all([
        loadContacts(),
        loadContactLists() // Refresh to update contact counts
        ]);
        setShowForm(false);
    } catch (err) {
        console.error('Failed to add contact:', err);
        setError('Failed to create contact. Please try again.');
    } finally {
        setLoading(false);
    }
    };

    const updateContact = async (contactData) => {
        try {
        setLoading(true);
        await contactsAPI.updateContact(editingContact.id, contactData);
        await Promise.all([
            loadContacts(),
            loadContactLists() // Refresh to update contact counts
        ]); // Refresh the list
        setEditingContact(null);
        setShowForm(false);
        
        // Update selected contact if it's the one being edited
        if (selectedContact && selectedContact.id === editingContact.id) {
            const updatedContact = await contactsAPI.getContact(editingContact.id);
            setSelectedContact(updatedContact);
        }
        } catch (err) {
        console.error('Failed to update contact:', err);
        setError('Failed to update contact. Please try again.');
        } finally {
        setLoading(false);
        }
    };

    const deleteContact = async (contactId) => {
        if (!window.confirm('Are you sure you want to delete this contact?')) {
        return;
        }

        try {
        setLoading(true);
        await contactsAPI.deleteContact(contactId);
        await Promise.all([
            loadContacts(),
            loadContactLists() // Refresh to update contact counts
        ]);
        
        // Clear selected contact if it was deleted
        if (selectedContact && selectedContact.id === contactId) {
            setSelectedContact(null);
        }
        
        // Remove from favorites
        if (favorites.has(contactId)) {
            const newFavorites = new Set(favorites);
            newFavorites.delete(contactId);
            setFavorites(newFavorites);
        }
        } catch (err) {
        console.error('Failed to delete contact:', err);
        setError('Failed to delete contact. Please try again.');
        } finally {
        setLoading(false);
        }
    };

    const toggleFavorite = async (contactId) => {
        try {
        const result = await contactsAPI.toggleFavorite(contactId);
        
        // Update local favorites state
        const newFavorites = new Set(favorites);
        if (result.is_favorite) {
            newFavorites.add(contactId);
        } else {
            newFavorites.delete(contactId);
        }
        setFavorites(newFavorites);
        } catch (err) {
        console.error('Failed to toggle favorite:', err);
        setError('Failed to update favorite status.');
        }
    };

    const exportContacts = async () => {
        try {
        await contactsAPI.downloadExport();
        } catch (err) {
        console.error('Failed to export contacts:', err);
        setError('Failed to export contacts. Please try again.');
        }
    };

    const importContacts = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        try {
        setLoading(true);
        const text = await file.text();
        const importedData = JSON.parse(text);
        
        // Handle different import formats
        let contactsToImport = [];
        if (importedData.contacts) {
            // New export format
            contactsToImport = importedData.contacts;
        } else if (Array.isArray(importedData)) {
            // Direct array format
            contactsToImport = importedData;
        } else {
            throw new Error('Invalid import file format');
        }

        // Import each contact
        let successCount = 0;
        let failCount = 0;

        for (const contact of contactsToImport) {
        try {
            await contactsAPI.createContact({
            name: contact.name,
            email: contact.email,
            phone: contact.phone,
            company: contact.company,
            category: contact.category || 'other',
            address: contact.address || null,
            notes: contact.notes || null,
            last_contact_date: contact.last_contact_date || contact.lastContact,
            contact_list_id: selectedListId  // Add this line
            });
            successCount++;
        } catch (err) {
            console.error('Failed to import contact:', contact, err);
            failCount++;
        }
        }

        await Promise.all([
            loadContacts(),
            loadContactLists() // Refresh to update contact counts
        ]);
        alert(`Import completed! ${successCount} contacts imported successfully. ${failCount} failed.`);
        } catch (err) {
        console.error('Failed to import contacts:', err);
        setError('Failed to import contacts. Please check the file format.');
        } finally {
        setLoading(false);
        event.target.value = '';
        }
    };
    const createContactList = async (listData) => {
        try {
            setLoading(true);
            const newList = await contactsAPI.createContactList(listData);
            await loadContactLists();
            setSelectedListId(newList.id);
            setShowListForm(false);
        } catch (err) {
            console.error('Failed to create contact list:', err);
            setError('Failed to create contact list. Please try again.');
        } finally {
            setLoading(false);
        }
        };

    const handleMigration = async () => {
      try {
        setLoading(true);
        const result = await migrateFromLocalStorage(selectedListId); // Pass the selected list ID
        
        if (result.migrated) {
          alert(`Migration completed! ${result.successful} contacts migrated successfully.`);
          await Promise.all([
            loadContacts(),
            loadContactLists()
          ]);
          setShowMigration(false);
        } else {
          alert(`Migration failed: ${result.reason || result.error}`);
        }
      } catch (err) {
        console.error('Migration failed:', err);
        setError('Failed to migrate contacts from localStorage.');
      } finally {
        setLoading(false);
      }
    };

    // Error boundary component
    if (error && !apiConnected) {
        return (
        <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center', padding: '48px', backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)', maxWidth: '500px' }}>
            <WifiOff style={{ width: '64px', height: '64px', color: '#ef4444', margin: '0 auto 24px' }} />
            <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827', marginBottom: '16px' }}>Connection Error</h2>
            <p style={{ color: '#6b7280', marginBottom: '24px' }}>{error}</p>
            <button 
                onClick={initializeContactBook}
                style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '12px 24px',
                fontSize: '16px',
                fontWeight: '500',
                borderRadius: '6px',
                border: '1px solid transparent',
                backgroundColor: '#2563eb',
                color: 'white',
                cursor: 'pointer'
                }}
            >
                <Wifi style={{ width: '20px', height: '20px', marginRight: '8px' }} />
                Retry Connection
            </button>
            </div>
        </div>
        );
    }

    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }}>
        {/* Header */}
        <div style={{ backgroundColor: 'white', boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', borderBottom: '1px solid #e5e7eb' }}>
            <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 24px' }}>
            <div style={{ paddingTop: '16px', paddingBottom: '16px' }}>
                {/* Connection Status */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <h1 style={{ fontSize: '30px', fontWeight: 'bold', color: '#111827', margin: 0 }}>📞 Contact Book</h1>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {apiConnected ? (
                        <>
                        <Wifi style={{ width: '16px', height: '16px', color: '#059669' }} />
                        <span style={{ fontSize: '12px', color: '#059669' }}>Connected</span>
                        </>
                    ) : (
                        <>
                        <WifiOff style={{ width: '16px', height: '16px', color: '#dc2626' }} />
                        <span style={{ fontSize: '12px', color: '#dc2626' }}>Disconnected</span>
                        </>
                    )}
                    </div>
                </div>
                <p style={{ color: '#6b7280', marginTop: '4px', margin: 0 }}>Manage your property contacts and relationships</p>
                </div>

                {/* Migration Notice */}
                {showMigration && (
                <div style={{ 
                    backgroundColor: '#fef3c7', 
                    border: '1px solid #fbbf24', 
                    borderRadius: '8px', 
                    padding: '12px 16px', 
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <AlertCircle style={{ width: '20px', height: '20px', color: '#d97706' }} />
                    <div>
                        <p style={{ fontWeight: '500', color: '#92400e', margin: 0 }}>Migrate Your Contacts</p>
                        <p style={{ fontSize: '14px', color: '#92400e', margin: 0 }}>We found contacts in your browser storage. Import them to the database?</p>
                    </div>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                    <button 
                        onClick={handleMigration}
                        disabled={loading}
                        style={{
                        padding: '6px 12px',
                        fontSize: '14px',
                        borderRadius: '4px',
                        border: '1px solid #d97706',
                        backgroundColor: '#f59e0b',
                        color: 'white',
                        cursor: loading ? 'not-allowed' : 'pointer'
                        }}
                    >
                        {loading ? 'Migrating...' : 'Migrate'}
                    </button>
                    <button 
                        onClick={() => setShowMigration(false)}
                        style={{
                        padding: '6px 12px',
                        fontSize: '14px',
                        borderRadius: '4px',
                        border: '1px solid #d1d5db',
                        backgroundColor: 'white',
                        color: '#6b7280',
                        cursor: 'pointer'
                        }}
                    >
                        Later
                    </button>
                    </div>
                </div>
                )}

                {/* Error Message */}
                {error && apiConnected && (
                <div style={{ 
                    backgroundColor: '#fef2f2', 
                    border: '1px solid #fecaca', 
                    borderRadius: '8px', 
                    padding: '12px 16px', 
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <AlertCircle style={{ width: '20px', height: '20px', color: '#dc2626' }} />
                    <p style={{ color: '#dc2626', margin: 0 }}>{error}</p>
                    </div>
                    <button 
                    onClick={() => setError(null)}
                    style={{
                        padding: '4px',
                        border: 'none',
                        backgroundColor: 'transparent',
                        color: '#dc2626',
                        cursor: 'pointer'
                    }}
                    >
                    ✕
                    </button>
                </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <label style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
                        Contact List:
                    </label>
                    <select
                        value={selectedListId || ''}
                        onChange={(e) => setSelectedListId(e.target.value)}
                        disabled={loading}
                        style={{
                        padding: '6px 12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        fontSize: '14px',
                        minWidth: '200px',
                        backgroundColor: loading ? '#f9fafb' : 'white'
                        }}
                    >
                        {contactLists.map(list => (
                        <option key={list.id} value={list.id}>
                            {list.name} ({list.contact_count} contacts)
                        </option>
                        ))}
                    </select>
                    <button
                        onClick={() => setShowListForm(true)}
                        disabled={loading}
                        style={{
                        padding: '6px 12px',
                        fontSize: '14px',
                        fontWeight: '500',
                        borderRadius: '6px',
                        border: '1px solid #d1d5db',
                        backgroundColor: '#f3f4f6',
                        color: '#374151',
                        cursor: loading ? 'not-allowed' : 'pointer'
                        }}
                        title="Create new contact list"
                    >
                        <Plus style={{ width: '16px', height: '16px' }} />
                    </button>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                                    <label style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    padding: '8px 16px',
                    fontSize: '14px',
                    fontWeight: '500',
                    borderRadius: '6px',
                    border: '1px solid #d1d5db',
                    backgroundColor: '#f3f4f6',
                    color: '#374151',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s'
                    }}>
                    <Upload style={{ width: '16px', height: '16px', marginRight: '8px' }} />
                    Import
                    <input type="file" accept=".json" onChange={importContacts} style={{ display: 'none' }} />
                    </label>
                    <button 
                    onClick={exportContacts}
                    disabled={loading}
                    style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        padding: '8px 16px',
                        fontSize: '14px',
                        fontWeight: '500',
                        borderRadius: '6px',
                        border: '1px solid #d1d5db',
                        backgroundColor: '#f3f4f6',
                        color: '#374151',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        transition: 'background-color 0.2s'
                    }}
                    >
                    {loading ? <Loader2 style={{ width: '16px', height: '16px', marginRight: '8px', animation: 'spin 1s linear infinite' }} /> : <Download style={{ width: '16px', height: '16px', marginRight: '8px' }} />}
                    Export
                    </button>
                    <button 
                    onClick={() => {
                        setEditingContact(null);
                        setShowForm(true);
                    }}
                    disabled={loading}
                    style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        padding: '8px 16px',
                        fontSize: '14px',
                        fontWeight: '500',
                        borderRadius: '6px',
                        border: '1px solid transparent',
                        backgroundColor: '#2563eb',
                        color: 'white',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        transition: 'background-color 0.2s'
                    }}
                    >
                    <Plus style={{ width: '16px', height: '16px', marginRight: '8px' }} />
                    Add Contact
                    </button>
                    <UserMenu />
                </div>
                </div>
                
                {/* Search and Filter Bar */}
                <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                    <div style={{ position: 'relative', flex: 1, minWidth: '300px' }}>
                    <Search style={{ 
                        position: 'absolute', 
                        left: '12px', 
                        top: '50%', 
                        transform: 'translateY(-50%)', 
                        color: '#9ca3af', 
                        width: '20px', 
                        height: '20px' 
                    }} />
                    <input
                        type="text"
                        placeholder="Search contacts by name, email, company..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        disabled={loading}
                        style={{
                        width: '100%',
                        padding: '8px 12px 8px 40px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        fontSize: '14px',
                        transition: 'border-color 0.2s'
                        }}
                    />
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                    <select 
                        value={filterCategory} 
                        onChange={(e) => setFilterCategory(e.target.value)}
                        disabled={loading}
                        style={{
                        padding: '8px 12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        fontSize: '14px',
                        minWidth: '150px'
                        }}
                    >
                        {categories.map(cat => (
                        <option key={cat.value} value={cat.value}>
                            {cat.label} ({cat.count})
                        </option>
                        ))}
                    </select>
                    <button
                        onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                        disabled={loading}
                        style={{
                        padding: '8px 12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        backgroundColor: '#f3f4f6',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        fontSize: '18px'
                        }}
                        title={`Switch to ${viewMode === 'grid' ? 'list' : 'grid'} view`}
                    >
                        {viewMode === 'grid' ? '📋' : '⬜'}
                    </button>
                    </div>
                </div>
                </div>
            </div>
            </div>
        </div>

        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '32px 24px' }}>
            <div style={{ display: 'flex', gap: '32px' }}>
            {/* Contacts List */}
            <div style={{ flex: 1 }}>
                {loading && contacts.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '48px 0' }}>
                    <Loader2 style={{ width: '48px', height: '48px', color: '#2563eb', margin: '0 auto 16px', animation: 'spin 1s linear infinite' }} />
                    <h3 style={{ fontSize: '18px', fontWeight: '500', color: '#111827', marginBottom: '8px' }}>Loading contacts...</h3>
                    <p style={{ color: '#6b7280' }}>Please wait while we fetch your contacts from the server.</p>
                </div>
                ) : contacts.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '48px 0' }}>
                    <User style={{ width: '64px', height: '64px', color: '#d1d5db', margin: '0 auto 16px' }} />
                    <h3 style={{ fontSize: '18px', fontWeight: '500', color: '#111827', marginBottom: '8px' }}>No contacts found</h3>
                    <p style={{ color: '#6b7280', marginBottom: '16px' }}>
                    {searchTerm || filterCategory !== 'all' 
                        ? 'Try adjusting your search or filter criteria'
                        : 'Get started by adding your first contact'
                    }
                    </p>
                    {!searchTerm && filterCategory === 'all' && (
                    <button 
                        onClick={() => setShowForm(true)}
                        style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        padding: '8px 16px',
                        fontSize: '14px',
                        fontWeight: '500',
                        borderRadius: '6px',
                        border: '1px solid transparent',
                        backgroundColor: '#2563eb',
                        color: 'white',
                        cursor: 'pointer'
                        }}
                    >
                        <Plus style={{ width: '16px', height: '16px', marginRight: '8px' }} />
                        Add Your First Contact
                    </button>
                    )}
                </div>
                ) : (
                <div style={viewMode === 'grid' 
                    ? { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }
                    : { display: 'flex', flexDirection: 'column', gap: '16px' }
                }>
                    {contacts.map(contact => (
                    <ContactCard 
                        key={contact.id} 
                        contact={contact} 
                        onSelect={setSelectedContact}
                        onEdit={(contact) => {
                        setEditingContact(contact);
                        setShowForm(true);
                        }}
                        onDelete={deleteContact}
                        onToggleFavorite={toggleFavorite}
                        isFavorite={favorites.has(contact.id)}
                        viewMode={viewMode}
                        disabled={loading}
                    />
                    ))}
                </div>
                )}
            </div>

            {/* Contact Details Sidebar */}
            {selectedContact && (
                <div style={{ width: '320px' }}>
                <ContactDetails 
                    contact={selectedContact} 
                    onClose={() => setSelectedContact(null)}
                    onEdit={(contact) => {
                    setEditingContact(contact);
                    setShowForm(true);
                    }}
                    onDelete={deleteContact}
                    onToggleFavorite={toggleFavorite}
                    isFavorite={favorites.has(selectedContact.id)}
                    disabled={loading}
                />
                </div>
            )}
            </div>
        </div>

        {/* Contact Form Modal */}
        {showForm && (
            <ContactForm
            contact={editingContact}
            onSubmit={editingContact ? updateContact : addContact}
            onCancel={() => {
                setShowForm(false);
                setEditingContact(null);
            }}
            loading={loading}
            />
        )}
        {showListForm && (
            <ContactListForm
                onSubmit={createContactList}
                onCancel={() => setShowListForm(false)}
                loading={loading}
            />
        )}
        </div>
    );
};

// Contact Card Component
const ContactCard = ({ contact, onSelect, onEdit, onDelete, onToggleFavorite, isFavorite, viewMode, disabled }) => {
  const getCategoryIcon = (category) => {
    const icons = {
      landlord: '🏠',
      tenant: '👤',
      contractor: '🔧',
      agent: '🏢',
      supplier: '📦',
      other: '📋'
    };
    return icons[category] || '👤';
  };

  const getCategoryColor = (category) => {
    const colors = {
      landlord: { bg: '#dbeafe', color: '#1e40af' },
      tenant: { bg: '#dcfce7', color: '#166534' },
      contractor: { bg: '#fed7aa', color: '#9a3412' },
      agent: { bg: '#f3e8ff', color: '#6b21a8' },
      supplier: { bg: '#fef3c7', color: '#92400e' },
      other: { bg: '#f3f4f6', color: '#1f2937' }
    };
    return colors[category] || { bg: '#f3f4f6', color: '#1f2937' };
  };

  const categoryColors = getCategoryColor(contact.category);

  if (viewMode === 'list') {
    return (
      <div style={{ 
        backgroundColor: 'white', 
        borderRadius: '8px', 
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
        border: '1px solid #e5e7eb', 
        padding: '16px',
        transition: 'box-shadow 0.2s',
        opacity: disabled ? 0.6 : 1
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1 }}>
            <div style={{ 
              width: '48px', 
              height: '48px', 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
              borderRadius: '50%', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              color: 'white', 
              fontWeight: '600', 
              fontSize: '18px' 
            }}>
              {contact.name.charAt(0).toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3 style={{ fontWeight: '600', color: '#111827', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{contact.name}</h3>
                <span style={{ 
                  padding: '2px 8px', 
                  borderRadius: '12px', 
                  fontSize: '12px', 
                  fontWeight: '500',
                  backgroundColor: categoryColors.bg,
                  color: categoryColors.color
                }}>
                  {getCategoryIcon(contact.category)} {contact.category}
                </span>
                {isFavorite && <Star style={{ width: '16px', height: '16px', color: '#eab308', fill: 'currentColor' }} />}
              </div>
              <p style={{ fontSize: '14px', color: '#6b7280', margin: '2px 0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{contact.company}</p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Phone style={{ width: '12px', height: '12px' }} />
                  {contact.phone}
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Mail style={{ width: '12px', height: '12px' }} />
                    {contact.email}
                </span>
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => onToggleFavorite(contact.id)}
              disabled={disabled}
              style={{
                padding: '4px',
                borderRadius: '4px',
                border: 'none',
                backgroundColor: 'transparent',
                color: isFavorite ? '#eab308' : '#9ca3af',
                cursor: disabled ? 'not-allowed' : 'pointer'
              }}
              title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
            >
              <Star style={{ width: '16px', height: '16px', fill: isFavorite ? 'currentColor' : 'none' }} />
            </button>
            <button
              onClick={() => onSelect(contact)}
              disabled={disabled}
              style={{
                padding: '4px 12px',
                fontSize: '12px',
                borderRadius: '4px',
                border: '1px solid #d1d5db',
                backgroundColor: '#f3f4f6',
                color: '#374151',
                cursor: disabled ? 'not-allowed' : 'pointer'
              }}
            >
              View
            </button>
            <button
              onClick={() => onEdit(contact)}
              disabled={disabled}
              style={{
                padding: '4px',
                borderRadius: '4px',
                border: 'none',
                backgroundColor: 'transparent',
                color: '#9ca3af',
                cursor: disabled ? 'not-allowed' : 'pointer'
              }}
              title="Edit contact"
            >
              <Edit2 style={{ width: '16px', height: '16px' }} />
            </button>
            <button
              onClick={() => onDelete(contact.id)}
              disabled={disabled}
              style={{
                padding: '4px',
                borderRadius: '4px',
                border: 'none',
                backgroundColor: 'transparent',
                color: '#9ca3af',
                cursor: disabled ? 'not-allowed' : 'pointer'
              }}
              title="Delete contact"
            >
              <Trash2 style={{ width: '16px', height: '16px' }} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      backgroundColor: 'white', 
      borderRadius: '8px', 
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
      border: '1px solid #e5e7eb', 
      padding: '24px',
      transition: 'box-shadow 0.2s, transform 0.2s',
      cursor: disabled ? 'not-allowed' : 'pointer',
      position: 'relative',
      opacity: disabled ? 0.6 : 1
    }}>
      <button
        onClick={() => onToggleFavorite(contact.id)}
        disabled={disabled}
        style={{
          position: 'absolute',
          top: '16px',
          right: '16px',
          padding: '4px',
          borderRadius: '4px',
          border: 'none',
          backgroundColor: 'transparent',
          color: isFavorite ? '#eab308' : '#d1d5db',
          cursor: disabled ? 'not-allowed' : 'pointer'
        }}
        title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
      >
        <Star style={{ width: '20px', height: '20px', fill: isFavorite ? 'currentColor' : 'none' }} />
      </button>

      <div onClick={() => !disabled && onSelect(contact)} style={{ marginBottom: '16px' }}>
        <div style={{ 
          width: '64px', 
          height: '64px', 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
          borderRadius: '50%', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          color: 'white', 
          fontWeight: 'bold', 
          fontSize: '24px', 
          margin: '0 auto 16px' 
        }}>
          {contact.name.charAt(0).toUpperCase()}
        </div>
        
        <h3 style={{ fontWeight: '600', fontSize: '18px', color: '#111827', textAlign: 'center', marginBottom: '8px' }}>{contact.name}</h3>
        
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
          <span style={{ 
            padding: '4px 12px', 
            borderRadius: '12px', 
            fontSize: '14px', 
            fontWeight: '500',
            backgroundColor: categoryColors.bg,
            color: categoryColors.color
          }}>
            {getCategoryIcon(contact.category)} {contact.category}
          </span>
        </div>
        
        <p style={{ fontSize: '14px', color: '#6b7280', textAlign: 'center', marginBottom: '12px' }}>{contact.company}</p>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '14px', color: '#6b7280' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <Phone style={{ width: '16px', height: '16px' }} />
            <span>{contact.phone}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <Mail style={{ width: '16px', height: '16px' }} />
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{contact.email}</span>
          </div>
        </div>
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', paddingTop: '16px', borderTop: '1px solid #e5e7eb' }}>
        <button
          onClick={() => onEdit(contact)}
          disabled={disabled}
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '6px 12px',
            fontSize: '14px',
            borderRadius: '4px',
            border: '1px solid #d1d5db',
            backgroundColor: '#f3f4f6',
            color: '#374151',
            cursor: disabled ? 'not-allowed' : 'pointer'
          }}
        >
          <Edit2 style={{ width: '12px', height: '12px', marginRight: '4px' }} />
          Edit
        </button>
        <button
          onClick={() => onDelete(contact.id)}
          disabled={disabled}
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '6px 12px',
            fontSize: '14px',
            borderRadius: '4px',
            border: '1px solid #fecaca',
            backgroundColor: '#fef2f2',
            color: '#dc2626',
            cursor: disabled ? 'not-allowed' : 'pointer'
          }}
        >
          <Trash2 style={{ width: '12px', height: '12px', marginRight: '4px' }} />
          Delete
        </button>
      </div>
    </div>
  );
};

// Contact Details Component
const ContactDetails = ({ contact, onClose, onEdit, onDelete, onToggleFavorite, isFavorite, disabled }) => {
  const getCategoryIcon = (category) => {
    const icons = {
      landlord: '🏠',
      tenant: '👤',
      contractor: '🔧',
      agent: '🏢',
      supplier: '📦',
      other: '📋'
    };
    return icons[category] || '👤';
  };

  const getCategoryColor = (category) => {
    const colors = {
      landlord: { bg: '#dbeafe', color: '#1e40af' },
      tenant: { bg: '#dcfce7', color: '#166534' },
      contractor: { bg: '#fed7aa', color: '#9a3412' },
      agent: { bg: '#f3e8ff', color: '#6b21a8' },
      supplier: { bg: '#fef3c7', color: '#92400e' },
      other: { bg: '#f3f4f6', color: '#1f2937' }
    };
    return colors[category] || { bg: '#f3f4f6', color: '#1f2937' };
  };

  const categoryColors = getCategoryColor(contact.category);

  return (
    <div style={{ 
      backgroundColor: 'white', 
      borderRadius: '8px', 
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)', 
      border: '1px solid #e5e7eb', 
      position: 'sticky',
      top: '24px',
      maxHeight: 'calc(100vh - 48px)',
      overflowY: 'auto'
    }}>
      {/* Header */}
      <div style={{ 
        padding: '24px 24px 16px', 
        borderBottom: '1px solid #e5e7eb',
        position: 'relative'
      }}>
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            padding: '4px',
            border: 'none',
            backgroundColor: 'transparent',
            color: '#9ca3af',
            cursor: 'pointer',
            borderRadius: '4px'
          }}
        >
          <X style={{ width: '20px', height: '20px' }} />
        </button>

        <div style={{ 
          width: '80px', 
          height: '80px', 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
          borderRadius: '50%', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          color: 'white', 
          fontWeight: 'bold', 
          fontSize: '32px', 
          margin: '0 auto 16px' 
        }}>
          {contact.name.charAt(0).toUpperCase()}
        </div>

        <h2 style={{ 
          fontSize: '24px', 
          fontWeight: '600', 
          color: '#111827', 
          textAlign: 'center', 
          marginBottom: '8px' 
        }}>
          {contact.name}
        </h2>

        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px' }}>
          <span style={{ 
            padding: '4px 12px', 
            borderRadius: '12px', 
            fontSize: '14px', 
            fontWeight: '500',
            backgroundColor: categoryColors.bg,
            color: categoryColors.color
          }}>
            {getCategoryIcon(contact.category)} {contact.category}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px' }}>
          <button
            onClick={() => onToggleFavorite(contact.id)}
            disabled={disabled}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '6px 12px',
              fontSize: '14px',
              borderRadius: '4px',
              border: '1px solid #d1d5db',
              backgroundColor: isFavorite ? '#fef3c7' : '#f3f4f6',
              color: isFavorite ? '#92400e' : '#374151',
              cursor: disabled ? 'not-allowed' : 'pointer'
            }}
          >
            <Star style={{ 
              width: '16px', 
              height: '16px', 
              marginRight: '4px',
              fill: isFavorite ? 'currentColor' : 'none'
            }} />
            {isFavorite ? 'Favorited' : 'Favorite'}
          </button>
          <button
            onClick={() => onEdit(contact)}
            disabled={disabled}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '6px 12px',
              fontSize: '14px',
              borderRadius: '4px',
              border: '1px solid #d1d5db',
              backgroundColor: '#f3f4f6',
              color: '#374151',
              cursor: disabled ? 'not-allowed' : 'pointer'
            }}
          >
            <Edit2 style={{ width: '16px', height: '16px', marginRight: '4px' }} />
            Edit
          </button>
        </div>
      </div>

      {/* Contact Information */}
      <div style={{ padding: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Company */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Building style={{ width: '20px', height: '20px', color: '#6b7280' }} />
            <div>
              <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>Company</p>
              <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: 0 }}>
                {contact.company || 'Not specified'}
              </p>
            </div>
          </div>

          {/* Phone */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Phone style={{ width: '20px', height: '20px', color: '#6b7280' }} />
            <div>
              <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>Phone</p>
              <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: 0 }}>
                <a href={`tel:${contact.phone}`} style={{ color: '#2563eb', textDecoration: 'none' }}>
                  {contact.phone}
                </a>
              </p>
            </div>
          </div>

          {/* Email */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Mail style={{ width: '20px', height: '20px', color: '#6b7280' }} />
            <div>
              <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>Email</p>
              <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: 0 }}>
                <a href={`mailto:${contact.email}`} style={{ color: '#2563eb', textDecoration: 'none' }}>
                  {contact.email}
                </a>
              </p>
            </div>
          </div>

          {/* Address */}
          {contact.address && (
            <div style={{ display: 'flex', alignItems: 'start', gap: '12px' }}>
              <MapPin style={{ width: '20px', height: '20px', color: '#6b7280', marginTop: '2px' }} />
              <div>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>Address</p>
                <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: 0, lineHeight: '1.4' }}>
                  {contact.address}
                </p>
              </div>
            </div>
          )}

          {/* Last Contact */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Calendar style={{ width: '20px', height: '20px', color: '#6b7280' }} />
            <div>
              <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>Last Contact</p>
              <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: 0 }}>
                {new Date(contact.last_contact_date).toLocaleDateString()}
              </p>
            </div>
          </div>

          {/* Notes */}
          {contact.notes && (
            <div style={{ display: 'flex', alignItems: 'start', gap: '12px' }}>
              <MessageSquare style={{ width: '20px', height: '20px', color: '#6b7280', marginTop: '2px' }} />
              <div>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>Notes</p>
                <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: 0, lineHeight: '1.4' }}>
                  {contact.notes}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid #e5e7eb' }}>
          <button
            onClick={() => onDelete(contact.id)}
            disabled={disabled}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '8px 16px',
              fontSize: '14px',
              borderRadius: '4px',
              border: '1px solid #fecaca',
              backgroundColor: '#fef2f2',
              color: '#dc2626',
              cursor: disabled ? 'not-allowed' : 'pointer'
            }}
          >
            <Trash2 style={{ width: '16px', height: '16px', marginRight: '8px' }} />
            Delete Contact
          </button>
        </div>
      </div>
    </div>
  );
};

// Contact Form Component
const ContactForm = ({ contact, onSubmit, onCancel, loading }) => {
  const [formData, setFormData] = useState({
    name: contact?.name || '',
    email: contact?.email || '',
    phone: contact?.phone || '',
    company: contact?.company || '',
    category: contact?.category || 'other',
    address: contact?.address || '',
    notes: contact?.notes || '',
    last_contact_date: contact?.last_contact_date?.split('T')[0] || new Date().toISOString().split('T')[0]
  });

  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (!formData.phone.trim()) {
      newErrors.phone = 'Phone number is required';
    }
    
    if (!formData.company.trim()) {
      newErrors.company = 'Company is required';
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
      await onSubmit(formData);
    } catch (error) {
      console.error('Form submission error:', error);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        width: '100%',
        maxWidth: '500px',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
      }}>
        {/* Header */}
        <div style={{
          padding: '24px 24px 16px',
          borderBottom: '1px solid #e5e7eb',
          position: 'sticky',
          top: 0,
          backgroundColor: 'white',
          zIndex: 1
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#111827', margin: 0 }}>
              {contact ? 'Edit Contact' : 'Add New Contact'}
            </h2>
            <button
              onClick={onCancel}
              disabled={loading}
              style={{
                padding: '4px',
                border: 'none',
                backgroundColor: 'transparent',
                color: '#9ca3af',
                cursor: loading ? 'not-allowed' : 'pointer',
                borderRadius: '4px'
              }}
            >
              <X style={{ width: '24px', height: '24px' }} />
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ padding: '24px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            
            {/* Name */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                color: '#111827', 
                marginBottom: '6px' 
              }}>
                Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: `1px solid ${errors.name ? '#f87171' : '#d1d5db'}`,
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white'
                }}
                placeholder="Enter full name"
              />
              {errors.name && (
                <p style={{ color: '#dc2626', fontSize: '12px', margin: '4px 0 0' }}>
                  {errors.name}
                </p>
              )}
            </div>

            {/* Email */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                color: '#111827', 
                marginBottom: '6px' 
              }}>
                Email *
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: `1px solid ${errors.email ? '#f87171' : '#d1d5db'}`,
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white'
                }}
                placeholder="Enter email address"
              />
              {errors.email && (
                <p style={{ color: '#dc2626', fontSize: '12px', margin: '4px 0 0' }}>
                  {errors.email}
                </p>
              )}
            </div>

            {/* Phone */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                color: '#111827', 
                marginBottom: '6px' 
              }}>
                Phone *
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: `1px solid ${errors.phone ? '#f87171' : '#d1d5db'}`,
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white'
                }}
                placeholder="Enter phone number"
              />
              {errors.phone && (
                <p style={{ color: '#dc2626', fontSize: '12px', margin: '4px 0 0' }}>
                  {errors.phone}
                </p>
              )}
            </div>

            {/* Company */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                color: '#111827', 
                marginBottom: '6px' 
              }}>
                Company *
              </label>
              <input
                type="text"
                value={formData.company}
                onChange={(e) => handleChange('company', e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: `1px solid ${errors.company ? '#f87171' : '#d1d5db'}`,
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white'
                }}
                placeholder="Enter company name"
              />
              {errors.company && (
                <p style={{ color: '#dc2626', fontSize: '12px', margin: '4px 0 0' }}>
                  {errors.company}
                </p>
              )}
            </div>

            {/* Category */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                color: '#111827', 
                marginBottom: '6px' 
              }}>
                Category
              </label>
              <select
                value={formData.category}
                onChange={(e) => handleChange('category', e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white'
                }}
              >
                <option value="landlord">🏠 Landlord</option>
                <option value="tenant">👤 Tenant</option>
                <option value="contractor">🔧 Contractor</option>
                <option value="agent">🏢 Agent</option>
                <option value="supplier">📦 Supplier</option>
                <option value="other">📋 Other</option>
              </select>
            </div>

            {/* Address */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                color: '#111827', 
                marginBottom: '6px' 
              }}>
                Address
              </label>
              <textarea
                value={formData.address}
                onChange={(e) => handleChange('address', e.target.value)}
                disabled={loading}
                rows={3}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white',
                  resize: 'vertical'
                }}
                placeholder="Enter address (optional)"
              />
            </div>

            {/* Last Contact Date */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                color: '#111827', 
                marginBottom: '6px' 
              }}>
                Last Contact Date
              </label>
              <input
                type="date"
                value={formData.last_contact_date}
                onChange={(e) => handleChange('last_contact_date', e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white'
                }}
              />
            </div>

            {/* Notes */}
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                color: '#111827', 
                marginBottom: '6px' 
              }}>
                Notes
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => handleChange('notes', e.target.value)}
                disabled={loading}
                rows={4}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white',
                  resize: 'vertical'
                }}
                placeholder="Add any notes about this contact (optional)"
              />
            </div>
          </div>

          {/* Form Actions */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'flex-end',
            gap: '12px',
            marginTop: '32px',
            paddingTop: '20px',
            borderTop: '1px solid #e5e7eb'
          }}>
            <button
              type="button"
              onClick={onCancel}
              disabled={loading}
              style={{
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: '500',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                backgroundColor: 'white',
                color: '#374151',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: '500',
                borderRadius: '6px',
                border: '1px solid transparent',
                backgroundColor: '#2563eb',
                color: 'white',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? (
                <>
                  <Loader2 style={{ width: '16px', height: '16px', marginRight: '8px', animation: 'spin 1s linear infinite' }} />
                  {contact ? 'Updating...' : 'Creating...'}
                </>
              ) : (
                <>
                  {contact ? 'Update Contact' : 'Create Contact'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const ContactListForm = ({ onSubmit, onCancel, loading }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });

  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = 'List name is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Form submission error:', error);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        width: '100%',
        maxWidth: '400px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
      }}>
        <div style={{
          padding: '24px 24px 16px',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#111827', margin: 0 }}>
              Create Contact List
            </h2>
            <button
              onClick={onCancel}
              disabled={loading}
              style={{
                padding: '4px',
                border: 'none',
                backgroundColor: 'transparent',
                color: '#9ca3af',
                cursor: loading ? 'not-allowed' : 'pointer',
                borderRadius: '4px'
              }}
            >
              <X style={{ width: '24px', height: '24px' }} />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '24px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                color: '#111827', 
                marginBottom: '6px' 
              }}>
                List Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: `1px solid ${errors.name ? '#f87171' : '#d1d5db'}`,
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white'
                }}
                placeholder="e.g., London Properties, Manchester Team"
              />
              {errors.name && (
                <p style={{ color: '#dc2626', fontSize: '12px', margin: '4px 0 0' }}>
                  {errors.name}
                </p>
              )}
            </div>

            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500', 
                color: '#111827', 
                marginBottom: '6px' 
              }}>
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                disabled={loading}
                rows={3}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white',
                  resize: 'vertical'
                }}
                placeholder="Optional description for this contact list"
              />
            </div>
          </div>

          <div style={{ 
            display: 'flex', 
            justifyContent: 'flex-end',
            gap: '12px',
            marginTop: '32px',
            paddingTop: '20px',
            borderTop: '1px solid #e5e7eb'
          }}>
            <button
              type="button"
              onClick={onCancel}
              disabled={loading}
              style={{
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: '500',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                backgroundColor: 'white',
                color: '#374151',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: '500',
                borderRadius: '6px',
                border: '1px solid transparent',
                backgroundColor: '#2563eb',
                color: 'white',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? (
                <>
                  <Loader2 style={{ width: '16px', height: '16px', marginRight: '8px', animation: 'spin 1s linear infinite' }} />
                  Creating...
                </>
              ) : (
                'Create List'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ContactBook_1;
