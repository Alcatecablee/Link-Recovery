import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { AlertCircle, Link2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

export const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleDemoLogin = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const success = await login();
      if (success) {
        navigate('/dashboard');
      } else {
        setError('Login failed. Please try again.');
      }
    } catch (err) {
      setError('An error occurred during login.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-4 text-center">
          <div className="mx-auto w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center">
            <Link2 className="w-8 h-8 text-white" />
          </div>
          <div>
            <CardTitle className="text-3xl font-bold">Link Recovery</CardTitle>
            <CardDescription className="text-base mt-2">
              Automated 404 Detection & Backlink Retention
            </CardDescription>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
              <p className="font-medium mb-1">✨ MVP Demo Mode</p>
              <p className="text-blue-600">
                Get instant access to explore the tool with sample data.
              </p>
            </div>
            
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <Button 
              onClick={handleDemoLogin}
              className="w-full h-12 text-base"
              size="lg"
              disabled={loading}
              data-testid="demo-login-btn"
            >
              {loading ? 'Signing in...' : 'Try Demo'}
            </Button>
          </div>
          
          <div className="text-center text-sm text-gray-500">
            <p>No signup required • Explore instantly</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};