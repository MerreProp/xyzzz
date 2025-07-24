/**
 * Contact Book API Utility Functions
 * Handles all API communication for the contact book feature
 */

const API_BASE = process.env.NODE_ENV === 'production' 
  ? '/api' 
  : 'http://localhost:8000/api';

// Generate or get session ID for favorites tracking
const getSessionId = () => {
  let sessionId = localStorage.getItem('contact-session-id');
  if (!sessionId) {
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('contact-session-id', sessionId);
  }
  return sessionId;
};

// Helper function to handle API responses
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  return response.json();
};

// Helper function to make API requests with proper headers
const apiRequest = async (url, options = {}) => {
  const sessionId = getSessionId();
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'x-session-id': sessionId,
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  const response = await fetch(`${API_BASE}${url}`, config);
  return handleResponse(response);
};

export const contactsAPI = {
  // ===================================================================
  // CONTACT OPERATIONS
  // ===================================================================

  /**
   * Get all contacts with optional filtering
   * @param {Object} filters - Filter options
   * @param {string} filters.search - Search term
   * @param {string} filters.category - Category filter
   * @param {string} filters.contact_list_id - Contact list filter
   * @param {number} filters.skip - Pagination skip
   * @param {number} filters.limit - Pagination limit
   */
  async getAllContacts(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.search) params.append('search', filters.search);
    if (filters.category && filters.category !== 'all') params.append('category', filters.category);
    if (filters.contact_list_id) params.append('contact_list_id', filters.contact_list_id);
    if (filters.skip) params.append('skip', filters.skip.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());

    const queryString = params.toString();
    const url = `/contacts/${queryString ? '?' + queryString : ''}`;
    
    return apiRequest(url);
  },

  /**
   * Get a specific contact by ID
   * @param {string} contactId - Contact ID
   */
  async getContact(contactId) {
    return apiRequest(`/contacts/${contactId}`);
  },

  /**
   * Create a new contact
   * @param {Object} contactData - Contact information
   * @param {string} contactData.name - Contact name
   * @param {string} contactData.email - Contact email
   * @param {string} contactData.phone - Contact phone
   * @param {string} contactData.company - Contact company
   * @param {string} contactData.category - Contact category
   * @param {string} contactData.address - Contact address (optional)
   * @param {string} contactData.notes - Contact notes (optional)
   * @param {string} contactListId - Contact list ID (optional)
   */
  async createContact(contactData, contactListId = null) {
    const url = contactListId 
      ? `/contacts/?contact_list_id=${contactListId}`
      : '/contacts/';
    
    return apiRequest(url, {
      method: 'POST',
      body: JSON.stringify(contactData),
    });
  },

  /**
   * Update an existing contact
   * @param {string} contactId - Contact ID
   * @param {Object} contactData - Updated contact information
   */
  async updateContact(contactId, contactData) {
    return apiRequest(`/contacts/${contactId}`, {
      method: 'PUT',
      body: JSON.stringify(contactData),
    });
  },

  /**
   * Delete a contact
   * @param {string} contactId - Contact ID
   */
  async deleteContact(contactId) {
    return apiRequest(`/contacts/${contactId}`, {
      method: 'DELETE',
    });
  },

  // ===================================================================
  // FAVORITES OPERATIONS
  // ===================================================================

  /**
   * Toggle favorite status for a contact
   * @param {string} contactId - Contact ID
   */
  async toggleFavorite(contactId) {
    return apiRequest(`/contacts/${contactId}/favorite`, {
      method: 'POST',
    });
  },

  /**
   * Get list of favorite contact IDs
   */
  async getFavorites() {
    const response = await apiRequest('/contacts/favorites/list');
    return response.favorites || [];
  },

  // ===================================================================
  // STATISTICS & ANALYTICS
  // ===================================================================

  /**
   * Get contact statistics
   * @param {string} contactListId - Contact list ID (optional)
   */
  async getContactStats(contactListId = null) {
    const url = contactListId 
      ? `/contacts/stats/summary?contact_list_id=${contactListId}`
      : '/contacts/stats/summary';
    
    return apiRequest(url);
  },

  // ===================================================================
  // CONTACT LISTS OPERATIONS
  // ===================================================================

  /**
   * Get all contact lists
   */
  async getContactLists() {
    return apiRequest('/contacts/lists/');
  },

  /**
   * Create a new contact list
   * @param {Object} listData - List information
   * @param {string} listData.name - List name
   * @param {string} listData.description - List description (optional)
   */
  async createContactList(listData) {
    return apiRequest('/contacts/lists/', {
      method: 'POST',
      body: JSON.stringify(listData),
    });
  },

  // ===================================================================
  // DATA MIGRATION & IMPORT/EXPORT
  // ===================================================================

  /**
   * Import contacts from localStorage data
   * @param {Array} localStorageContacts - Contacts from localStorage
   */
  async importFromLocalStorage(localStorageContacts) {
    const results = {
      successful: [],
      failed: [],
      total: localStorageContacts.length
    };

    for (const contact of localStorageContacts) {
      try {
        // Transform localStorage format to API format
        const contactData = {
          name: contact.name,
          email: contact.email,
          phone: contact.phone,
          company: contact.company,
          category: contact.category || 'other',
          address: contact.address || null,
          notes: contact.notes || null,
          last_contact_date: contact.lastContact || new Date().toISOString().split('T')[0]
        };

        const newContact = await this.createContact(contactData);
        results.successful.push(newContact);
      } catch (error) {
        console.error('Failed to import contact:', contact, error);
        results.failed.push({ contact, error: error.message });
      }
    }

    return results;
  },

  /**
   * Export contacts to JSON format
   * @param {Array} contacts - Contacts to export
   */
  async exportContacts(contacts = null) {
    if (!contacts) {
      contacts = await this.getAllContacts({ limit: 1000 });
    }

    const exportData = {
      exported_at: new Date().toISOString(),
      version: '1.0',
      total_contacts: contacts.length,
      contacts: contacts.map(contact => ({
        name: contact.name,
        email: contact.email,
        phone: contact.phone,
        company: contact.company,
        category: contact.category,
        address: contact.address,
        notes: contact.notes,
        last_contact_date: contact.last_contact_date,
        created_at: contact.created_at
      }))
    };

    return exportData;
  },

  /**
   * Download contacts as JSON file
   */
  async downloadExport() {
    const exportData = await this.exportContacts();
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `contacts-export-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  },

  // ===================================================================
  // UTILITY FUNCTIONS
  // ===================================================================

  /**
   * Check if the API is available
   */
  async healthCheck() {
    try {
      const response = await fetch(`${API_BASE}/contacts/health`);  // Fixed URL
      return response.ok;
    } catch (error) {
      console.error('API health check failed:', error);
      return false;
    }
  },
  
  /**
   * Get category options for forms
   */
  getCategoryOptions() {
    return [
      { value: 'landlord', label: '🏠 Landlord', description: 'Property owners and managers' },
      { value: 'tenant', label: '👤 Tenant', description: 'Current and prospective renters' },
      { value: 'contractor', label: '🔧 Contractor', description: 'Maintenance and repair services' },
      { value: 'agent', label: '🏢 Agent', description: 'Real estate agents and brokers' },
      { value: 'supplier', label: '📦 Supplier', description: 'Equipment and service providers' },
      { value: 'other', label: '📋 Other', description: 'Other business contacts' }
    ];
  },

  /**
   * Get filter options for category filtering
   */
  getFilterOptions() {
    return [
      { value: 'all', label: '👥 All Contacts' },
      ...this.getCategoryOptions()
    ];
  }
};

// ===================================================================
// ERROR HANDLING UTILITIES
// ===================================================================

export class ContactAPIError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = 'ContactAPIError';
    this.status = status;
    this.details = details;
  }
}

// ===================================================================
// MIGRATION HELPER
// ===================================================================

/**
 * Migrate existing localStorage contacts to the API
 * Call this once to move from Phase 0 (localStorage) to Phase 1 (API)
 */
export const migrateFromLocalStorage = async () => {
  try {
    // Get existing localStorage contacts
    const localContacts = localStorage.getItem('hmo-contacts');
    const localFavorites = localStorage.getItem('hmo-favorites');
    
    if (!localContacts) {
      console.log('No localStorage contacts found to migrate');
      return { migrated: false, reason: 'No data found' };
    }

    const contacts = JSON.parse(localContacts);
    const favorites = localFavorites ? JSON.parse(localFavorites) : [];

    console.log(`Found ${contacts.length} contacts to migrate`);

    // Import contacts
    const importResult = await contactsAPI.importFromLocalStorage(contacts);
    
    // Migrate favorites
    for (const contactId of favorites) {
      try {
        // Find the corresponding new contact by email (since IDs will be different)
        const originalContact = contacts.find(c => c.id === contactId);
        if (originalContact) {
          const allNewContacts = await contactsAPI.getAllContacts();
          const matchingContact = allNewContacts.find(c => c.email === originalContact.email);
          if (matchingContact) {
            await contactsAPI.toggleFavorite(matchingContact.id);
          }
        }
      } catch (error) {
        console.error('Failed to migrate favorite:', contactId, error);
      }
    }

    // Backup localStorage data
    localStorage.setItem('hmo-contacts-backup', localContacts);
    localStorage.setItem('hmo-favorites-backup', localFavorites || '[]');
    
    // Clear localStorage (optional - you might want to keep as backup)
    // localStorage.removeItem('hmo-contacts');
    // localStorage.removeItem('hmo-favorites');

    console.log('Migration completed:', importResult);
    
    return {
      migrated: true,
      successful: importResult.successful.length,
      failed: importResult.failed.length,
      total: importResult.total
    };

  } catch (error) {
    console.error('Migration failed:', error);
    return { migrated: false, error: error.message };
  }
};

export default contactsAPI;