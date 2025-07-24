import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { Users, UserPlus, Mail, Clock, Check, X, Shield, Edit3, Eye, Trash2 } from 'lucide-react';

const TeamManagement = ({ contactListId, contactListName }) => {
  const { apiRequest } = useAuth();
  const [members, setMembers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [invitePermission, setInvitePermission] = useState('viewer');
  const [inviteMessage, setInviteMessage] = useState('');

  useEffect(() => {
    loadTeamData();
  }, [contactListId]);

  const loadTeamData = async () => {
    try {
      const [membersData, invitationsData] = await Promise.all([
        apiRequest(`/team/lists/${contactListId}/members`),
        apiRequest(`/team/lists/${contactListId}/invitations`)
      ]);
      setMembers(membersData);
      setInvitations(invitationsData);
    } catch (error) {
      console.error('Failed to load team data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInviteUser = async () => {
    if (!inviteEmail) {
      alert('Please enter an email address');
      return;
    }
    
    try {
      await apiRequest(`/team/lists/${contactListId}/invite`, 'POST', {
        email: inviteEmail,
        permission_level: invitePermission,
        message: inviteMessage
      });
      
      setInviteEmail('');
      setInviteMessage('');
      setShowInviteForm(false);
      loadTeamData();
      
      alert('Invitation sent successfully!');
    } catch (error) {
      alert(`Failed to send invitation: ${error.message}`);
    }
  };

  const handleUpdatePermission = async (userId, newPermission) => {
    try {
      await apiRequest(`/team/lists/${contactListId}/members/${userId}/permission`, 'PUT', {
        user_id: userId,
        permission_level: newPermission
      });
      loadTeamData();
    } catch (error) {
      alert(`Failed to update permission: ${error.message}`);
    }
  };

  const handleRemoveMember = async (userId, userName) => {
    if (!window.confirm(`Are you sure you want to remove ${userName} from this contact list?`)) {
      return;
    }
    
    try {
      await apiRequest(`/team/lists/${contactListId}/members/${userId}`, 'DELETE');
      loadTeamData();
    } catch (error) {
      alert(`Failed to remove member: ${error.message}`);
    }
  };

  const getPermissionIcon = (permission) => {
    switch (permission) {
      case 'owner': 
        return <Shield size={16} style={{ color: '#dc2626' }} />;
      case 'editor': 
        return <Edit3 size={16} style={{ color: '#d97706' }} />;
      case 'viewer': 
        return <Eye size={16} style={{ color: '#059669' }} />;
      default: 
        return <Eye size={16} style={{ color: '#6b7280' }} />;
    }
  };

  const getPermissionColor = (permission) => {
    switch (permission) {
      case 'owner': return '#dc2626';
      case 'editor': return '#d97706';
      case 'viewer': return '#059669';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ 
          width: '32px', 
          height: '32px', 
          margin: '0 auto',
          border: '3px solid #f3f4f6',
          borderTop: '3px solid #3b82f6',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
        <p style={{ marginTop: '1rem', color: '#6b7280' }}>Loading team data...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '2rem',
        paddingBottom: '1rem',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <div>
          <h2 style={{ 
            fontSize: '1.5rem', 
            fontWeight: '600', 
            color: '#111827', 
            margin: '0 0 0.5rem 0',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <Users size={24} />
            Team Management
          </h2>
          <p style={{ color: '#6b7280', margin: 0 }}>
            Manage access and permissions for "{contactListName}"
          </p>
        </div>
        <button
          onClick={() => setShowInviteForm(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1rem',
            backgroundColor: '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.875rem',
            fontWeight: '500'
          }}
        >
          <UserPlus size={16} />
          Invite Member
        </button>
      </div>

      {/* Invite Form Modal */}
      {showInviteForm && (
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
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '2rem',
            borderRadius: '8px',
            width: '100%',
            maxWidth: '500px',
            margin: '1rem'
          }}>
            <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: '600' }}>
              Invite Team Member
            </h3>
            
            <div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                  Email Address
                </label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                    boxSizing: 'border-box'
                  }}
                  placeholder="colleague@example.com"
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                  Permission Level
                </label>
                <select
                  value={invitePermission}
                  onChange={(e) => setInvitePermission(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                    boxSizing: 'border-box'
                  }}
                >
                  <option value="viewer">Viewer - Can view contacts</option>
                  <option value="editor">Editor - Can add and edit contacts</option>
                  <option value="owner">Owner - Full access and management</option>
                </select>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                  Message (Optional)
                </label>
                <textarea
                  value={inviteMessage}
                  onChange={(e) => setInviteMessage(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                    height: '80px',
                    resize: 'vertical',
                    boxSizing: 'border-box'
                  }}
                  placeholder="Optional message to include with the invitation..."
                />
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                <button
                  onClick={() => setShowInviteForm(false)}
                  style={{
                    padding: '0.75rem 1rem',
                    border: '1px solid #d1d5db',
                    backgroundColor: 'white',
                    color: '#374151',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '0.875rem'
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleInviteUser}
                  style={{
                    padding: '0.75rem 1rem',
                    backgroundColor: '#2563eb',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '0.875rem'
                  }}
                >
                  Send Invitation
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Current Members */}
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ 
          fontSize: '1.125rem', 
          fontWeight: '600', 
          marginBottom: '1rem',
          color: '#111827'
        }}>
          Team Members ({members.length})
        </h3>
        
        <div style={{
          backgroundColor: 'white',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          {members.map((member, index) => (
            <div
              key={member.user_id}
              style={{
                padding: '1rem',
                borderBottom: index < members.length - 1 ? '1px solid #f3f4f6' : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  backgroundColor: '#e5e7eb',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1rem',
                  fontWeight: '600',
                  color: '#374151'
                }}>
                  {member.full_name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p style={{ 
                    margin: 0, 
                    fontWeight: '500', 
                    color: '#111827',
                    fontSize: '0.875rem'
                  }}>
                    {member.full_name}
                  </p>
                  <p style={{ 
                    margin: 0, 
                    color: '#6b7280', 
                    fontSize: '0.75rem'
                  }}>
                    {member.email}
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {/* Permission Badge */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  padding: '0.25rem 0.75rem',
                  backgroundColor: `${getPermissionColor(member.permission_level)}20`,
                  borderRadius: '9999px',
                  fontSize: '0.75rem',
                  fontWeight: '500',
                  color: getPermissionColor(member.permission_level)
                }}>
                  {getPermissionIcon(member.permission_level)}
                  {member.permission_level}
                </div>

                {/* Actions */}
                {member.can_manage && (
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <select
                      value={member.permission_level}
                      onChange={(e) => handleUpdatePermission(member.user_id, e.target.value)}
                      style={{
                        padding: '0.25rem 0.5rem',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        fontSize: '0.75rem'
                      }}
                    >
                      <option value="viewer">Viewer</option>
                      <option value="editor">Editor</option>
                      <option value="owner">Owner</option>
                    </select>
                    <button
                      onClick={() => handleRemoveMember(member.user_id, member.full_name)}
                      style={{
                        padding: '0.25rem',
                        border: 'none',
                        backgroundColor: '#fef2f2',
                        color: '#dc2626',
                        borderRadius: '4px',
                        cursor: 'pointer'
                      }}
                      title="Remove member"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Pending Invitations */}
      {invitations.length > 0 && (
        <div>
          <h3 style={{ 
            fontSize: '1.125rem', 
            fontWeight: '600', 
            marginBottom: '1rem',
            color: '#111827'
          }}>
            Pending Invitations ({invitations.filter(inv => !inv.is_accepted && !inv.is_expired).length})
          </h3>
          
          <div style={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            {invitations.map((invitation, index) => (
              <div
                key={invitation.id}
                style={{
                  padding: '1rem',
                  borderBottom: index < invitations.length - 1 ? '1px solid #f3f4f6' : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  opacity: invitation.is_accepted || invitation.is_expired ? 0.6 : 1
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <Mail size={20} style={{ color: '#6b7280' }} />
                  <div>
                    <p style={{ 
                      margin: 0, 
                      fontWeight: '500', 
                      color: '#111827',
                      fontSize: '0.875rem'
                    }}>
                      {invitation.email}
                    </p>
                    <p style={{ 
                      margin: 0, 
                      color: '#6b7280', 
                      fontSize: '0.75rem'
                    }}>
                      Invited by {invitation.invited_by} • {invitation.permission_level}
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {invitation.is_accepted ? (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      color: '#059669',
                      fontSize: '0.75rem'
                    }}>
                      <Check size={14} />
                      Accepted
                    </div>
                  ) : invitation.is_expired ? (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      color: '#dc2626',
                      fontSize: '0.75rem'
                    }}>
                      <X size={14} />
                      Expired
                    </div>
                  ) : (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      color: '#d97706',
                      fontSize: '0.75rem'
                    }}>
                      <Clock size={14} />
                      Pending
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default TeamManagement;