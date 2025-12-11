import React, { useState, useEffect } from 'react';
import { errors as errorsApi } from '@/api/client';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ExternalLink, CheckCircle, XCircle, Sparkles, Loader2 } from 'lucide-react';

export const ErrorDetailModal = ({ error, open, onClose, onUpdate }) => {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    if (open && error) {
      loadDetails();
    }
  }, [open, error]);

  const loadDetails = async () => {
    try {
      const response = await errorsApi.getDetails(error.id);
      setDetails(response.data);
    } catch (err) {
      console.error('Failed to load error details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateRecommendations = async () => {
    setGenerating(true);
    try {
      const response = await errorsApi.generateRecommendations(error.id);
      setDetails({ ...details, recommendation: response.data.recommendation });
    } catch (err) {
      console.error('Failed to generate recommendations:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleMarkAsFixed = async () => {
    setUpdating(true);
    try {
      await errorsApi.updateStatus(error.id, 'fixed');
      onUpdate();
      onClose();
    } catch (err) {
      console.error('Failed to update status:', err);
    } finally {
      setUpdating(false);
    }
  };

  const handleMarkAsIgnored = async () => {
    setUpdating(true);
    try {
      await errorsApi.updateStatus(error.id, 'ignored');
      onUpdate();
      onClose();
    } catch (err) {
      console.error('Failed to update status:', err);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto" data-testid="error-detail-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span className="truncate pr-4">404 Error Details</span>
            <Badge variant={error.priority_score > 70 ? 'destructive' : 'secondary'}>
              Priority: {error.priority_score}
            </Badge>
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* URL Info */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">URL</label>
              <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                <ExternalLink className="w-4 h-4 text-gray-400" />
                <code className="text-sm flex-1 truncate">{details?.error?.url}</code>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <p className="text-sm text-gray-600">Backlinks</p>
                  <p className="text-2xl font-bold text-blue-600">{details?.error?.backlink_count || 0}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <p className="text-sm text-gray-600">Impressions</p>
                  <p className="text-2xl font-bold text-purple-600">{details?.error?.impressions || 0}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <p className="text-sm text-gray-600">Status</p>
                  <Badge className="mt-2" variant="outline">{details?.error?.status}</Badge>
                </CardContent>
              </Card>
            </div>

            {/* Tabs */}
            <Tabs defaultValue="recommendations" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="recommendations" data-testid="recommendations-tab">AI Recommendations</TabsTrigger>
                <TabsTrigger value="backlinks" data-testid="backlinks-tab">Backlinks ({details?.backlinks?.length || 0})</TabsTrigger>
              </TabsList>

              <TabsContent value="recommendations" className="space-y-4">
                {!details?.recommendation ? (
                  <Card>
                    <CardContent className="pt-6 text-center">
                      <Sparkles className="w-12 h-12 text-blue-600 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold mb-2">Generate AI Recommendations</h3>
                      <p className="text-gray-600 mb-4">
                        Get smart suggestions for redirect targets and content creation
                      </p>
                      <Button 
                        onClick={handleGenerateRecommendations} 
                        disabled={generating}
                        data-testid="generate-recommendations-btn"
                      >
                        {generating ? (
                          <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating...</>
                        ) : (
                          <><Sparkles className="w-4 h-4 mr-2" /> Generate Recommendations</>
                        )}
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="space-y-4">
                    {/* Redirect Recommendation */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Redirect Recommendation</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div>
                          <label className="text-sm font-medium text-gray-700">Suggested Target</label>
                          <div className="mt-1 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                            <code className="text-sm text-blue-900">
                              {details.recommendation.redirect_target || 'N/A'}
                            </code>
                          </div>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-700">Reason</label>
                          <p className="mt-1 text-sm text-gray-600">
                            {details.recommendation.redirect_reason || 'No reason provided'}
                          </p>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Content Suggestion */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Content Creation Suggestion</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-gray-700 leading-relaxed">
                          {details.recommendation.content_suggestion || 'No content suggestion available'}
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="backlinks" className="space-y-4">
                {details?.backlinks?.length === 0 ? (
                  <Alert>
                    <AlertDescription>
                      No backlinks found for this URL. The URL has {details?.error?.backlink_count || 0} backlinks according to GSC data.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <div className="space-y-2">
                    {details?.backlinks?.map((backlink) => (
                      <div key={backlink.id} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <ExternalLink className="w-4 h-4 text-gray-400" />
                          <code className="text-sm text-gray-700">{backlink.source_url}</code>
                        </div>
                        {backlink.anchor_text && (
                          <p className="text-sm text-gray-600 mt-1 ml-6">
                            Anchor: <span className="font-medium">{backlink.anchor_text}</span>
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </TabsContent>
            </Tabs>

            {/* Actions */}
            <div className="flex justify-between pt-4 border-t">
              <div className="space-x-2">
                <Button 
                  onClick={handleMarkAsFixed} 
                  disabled={updating}
                  variant="default"
                  data-testid="mark-fixed-btn"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Mark as Fixed
                </Button>
                <Button 
                  onClick={handleMarkAsIgnored} 
                  disabled={updating}
                  variant="outline"
                  data-testid="mark-ignored-btn"
                >
                  <XCircle className="w-4 h-4 mr-2" />
                  Ignore
                </Button>
              </div>
              <Button variant="ghost" onClick={onClose}>
                Close
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};