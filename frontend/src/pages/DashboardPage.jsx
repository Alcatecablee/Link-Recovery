import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { dashboard, sites, errors as errorsApi } from '@/api/client';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { AlertCircle, Link2, TrendingDown, CheckCircle, ExternalLink, Plus, RefreshCw } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ErrorDetailModal } from '@/components/ErrorDetailModal';

export const DashboardPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [sitesList, setSitesList] = useState([]);
  const [errorsList, setErrorsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addSiteOpen, setAddSiteOpen] = useState(false);
  const [newSiteUrl, setNewSiteUrl] = useState('');
  const [selectedError, setSelectedError] = useState(null);
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, sitesRes, errorsRes] = await Promise.all([
        dashboard.getStats(),
        sites.list(),
        errorsApi.list({ status: 'new' })
      ]);
      
      setStats(statsRes.data);
      setSitesList(sitesRes.data.sites);
      setErrorsList(errorsRes.data.errors);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSite = async () => {
    if (!newSiteUrl) return;
    
    try {
      await sites.create(newSiteUrl);
      setNewSiteUrl('');
      setAddSiteOpen(false);
      loadData();
    } catch (error) {
      console.error('Failed to add site:', error);
    }
  };

  const handleScan = async (siteId) => {
    setScanning(true);
    try {
      await sites.scan(siteId);
      await loadData();
    } catch (error) {
      console.error('Scan failed:', error);
    } finally {
      setScanning(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50" data-testid="dashboard-page">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <Link2 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Link Recovery</h1>
                <p className="text-sm text-gray-500">{user?.email}</p>
              </div>
            </div>
            <Button onClick={handleLogout} variant="outline" data-testid="logout-btn">
              Logout
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total 404s</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{stats?.total_errors || 0}</p>
                </div>
                <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                  <AlertCircle className="w-6 h-6 text-red-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">New Issues</p>
                  <p className="text-3xl font-bold text-orange-600 mt-1">{stats?.new_errors || 0}</p>
                </div>
                <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                  <TrendingDown className="w-6 h-6 text-orange-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Fixed</p>
                  <p className="text-3xl font-bold text-green-600 mt-1">{stats?.fixed_errors || 0}</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Backlinks</p>
                  <p className="text-3xl font-bold text-blue-600 mt-1">{stats?.backlinks_affected || 0}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <ExternalLink className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sites Section */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Your Sites</CardTitle>
              <Button onClick={() => setAddSiteOpen(true)} size="sm" data-testid="add-site-btn">
                <Plus className="w-4 h-4 mr-2" />
                Add Site
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {sitesList.length === 0 ? (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  No sites added yet. Add your first site to start monitoring 404 errors.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-3">
                {sitesList.map((site) => (
                  <div key={site.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">{site.site_url}</p>
                      <p className="text-sm text-gray-500">
                        Last scan: {site.last_scan ? new Date(site.last_scan).toLocaleDateString() : 'Never'}
                      </p>
                    </div>
                    <Button 
                      onClick={() => handleScan(site.id)} 
                      size="sm" 
                      disabled={scanning}
                      data-testid={`scan-site-${site.id}`}
                    >
                      <RefreshCw className={`w-4 h-4 mr-2 ${scanning ? 'animate-spin' : ''}`} />
                      {scanning ? 'Scanning...' : 'Scan Now'}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 404 Errors List */}
        <Card>
          <CardHeader>
            <CardTitle>Recent 404 Errors</CardTitle>
          </CardHeader>
          <CardContent>
            {errorsList.length === 0 ? (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  No 404 errors found. Run a scan to check for issues.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-3">
                {errorsList.slice(0, 10).map((error) => (
                  <div 
                    key={error.id} 
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                    onClick={() => setSelectedError(error)}
                    data-testid={`error-item-${error.id}`}
                  >
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 truncate">{error.url}</p>
                      <div className="flex items-center space-x-4 mt-1">
                        <span className="text-sm text-gray-500">
                          {error.backlink_count} backlinks
                        </span>
                        <span className="text-sm text-gray-500">
                          {error.impressions} impressions
                        </span>
                      </div>
                    </div>
                    <Badge variant={error.priority_score > 70 ? 'destructive' : 'secondary'}>
                      Priority: {error.priority_score}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Add Site Dialog */}
      <Dialog open={addSiteOpen} onOpenChange={setAddSiteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Site</DialogTitle>
            <DialogDescription>
              Enter the URL of the site you want to monitor for 404 errors.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label htmlFor="site-url">Site URL</Label>
              <Input
                id="site-url"
                placeholder="https://example.com"
                value={newSiteUrl}
                onChange={(e) => setNewSiteUrl(e.target.value)}
                data-testid="site-url-input"
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setAddSiteOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddSite} data-testid="submit-add-site">
                Add Site
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Error Detail Modal */}
      {selectedError && (
        <ErrorDetailModal
          error={selectedError}
          open={!!selectedError}
          onClose={() => setSelectedError(null)}
          onUpdate={loadData}
        />
      )}
    </div>
  );
};