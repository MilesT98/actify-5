import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const CameraCapture = ({ onCapture, onClose, darkMode }) => {
  const [stream, setStream] = useState(null);
  const [isCapturing, setIsCapturing] = useState(false);

  useEffect(() => {
    startCamera();
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const startCamera = async () => {
    try {
      const constraints = {
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1080 },
          height: { ideal: 1920 }
        },
        audio: false
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(mediaStream);
      
      const video = document.getElementById('camera-video');
      if (video) {
        video.srcObject = mediaStream;
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
      alert('Failed to access camera. Please check permissions.');
      onClose();
    }
  };

  const capturePhoto = () => {
    const video = document.getElementById('camera-video');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    canvas.toBlob((blob) => {
      onCapture(blob);
    }, 'image/jpeg', 0.8);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black">
      <div className="relative h-full">
        <video
          id="camera-video"
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />
        
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex space-x-4">
          <button
            onClick={onClose}
            className="bg-gray-600 text-white p-4 rounded-full"
          >
            Cancel
          </button>
          <button
            onClick={capturePhoto}
            className="bg-white p-6 rounded-full border-4 border-gray-300"
          >
            📷
          </button>
        </div>
      </div>
    </div>
  );
};

const AuthScreen = ({ onLogin, darkMode }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    full_name: '',
    email: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const endpoint = isLogin ? '/login' : '/users';
      const response = await axios.post(`${API}${endpoint}`, formData);
      
      if (isLogin) {
        if (response.data.message === "Login successful") {
          // Secure token storage
          const { user, session_id } = response.data;
          localStorage.setItem('actify_user', JSON.stringify(user));
          localStorage.setItem('actify_session', session_id);
          localStorage.setItem('actify_auth_timestamp', new Date().getTime().toString());
          
          setSuccess('Login successful! Welcome back! 🎉');
          
          // Brief delay to show success message before redirection
          setTimeout(() => {
            onLogin(user);
          }, 500); // Brief delay to show success message
          
        } else {
          setError(response.data.message || response.data.detail || 'Login failed. Please check your credentials.');
        }
      } else {
        setSuccess('Account created successfully! Please log in.');
        setIsLogin(true);
        setFormData({ username: '', password: '', full_name: '', email: '' });
      }
    } catch (error) {
      console.error('Auth error:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);
      setError(error.response?.data?.detail || error.response?.data?.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-500 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">ACTIFY</h1>
          <p className="text-gray-600 dark:text-gray-300">Transform your fitness journey</p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="text"
              placeholder="Username"
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              required
            />
          </div>

          <div>
            <input
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              required
            />
          </div>

          {!isLogin && (
            <>
              <div>
                <input
                  type="text"
                  placeholder="Full Name"
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  required
                />
              </div>

              <div>
                <input
                  type="email"
                  placeholder="Email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  required
                />
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-purple-600 text-white p-3 rounded-lg font-semibold hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
              setSuccess('');
              setFormData({ username: '', password: '', full_name: '', email: '' });
            }}
            className="text-purple-600 hover:text-purple-700 font-medium"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
};

// Enhanced FeedScreen with Global and Group Activity Feeds
const FeedScreen = ({ user }) => {
  const [homeActiveTab, setHomeActiveTab] = useState('friends');
  const [dailyGlobalActivity, setDailyGlobalActivity] = useState(null);
  const [globalFeed, setGlobalFeed] = useState(null);
  const [userGroups, setUserGroups] = useState([]);
  const [groupFeeds, setGroupFeeds] = useState({});
  const [loading, setLoading] = useState(true);
  
  // Global activity submission state
  const [showGlobalSubmission, setShowGlobalSubmission] = useState(false);
  const [globalSubmissionText, setGlobalSubmissionText] = useState('');
  const [globalPhotoPreview, setGlobalPhotoPreview] = useState(null);
  const [globalPhotoFile, setGlobalPhotoFile] = useState(null);
  const [showGlobalCamera, setShowGlobalCamera] = useState(false);
  
  // Group activity submission state
  const [showGroupSubmission, setShowGroupSubmission] = useState(null);
  const [groupSubmissionText, setGroupSubmissionText] = useState('');
  const [groupPhotoPreview, setGroupPhotoPreview] = useState(null);
  const [groupPhotoFile, setGroupPhotoFile] = useState(null);
  const [showGroupCamera, setShowGroupCamera] = useState(false);

  const loadDailyGlobalActivity = async () => {
    try {
      const response = await axios.get(`${API}/daily-global-activity/current`);
      setDailyGlobalActivity(response.data);
    } catch (error) {
      console.error('Failed to load daily global activity:', error);
    }
  };

  const loadGlobalFeed = async () => {
    try {
      const response = await axios.get(`${API}/daily-global-activity/feed?user_id=${user.id}&friends_only=true`);
      setGlobalFeed(response.data);
    } catch (error) {
      console.error('Failed to load global feed:', error);
    }
  };

  const loadUserGroups = async () => {
    try {
      const response = await axios.get(`${API}/users/${user.id}/groups`);
      setUserGroups(response.data || []);
      
      // Load group feeds for each group
      for (const group of response.data || []) {
        loadGroupFeed(group.id);
      }
    } catch (error) {
      console.error('Failed to load user groups:', error);
    }
  };

  const loadGroupFeed = async (groupId) => {
    try {
      const response = await axios.get(`${API}/groups/${groupId}/daily-activity-feed?user_id=${user.id}`);
      setGroupFeeds(prev => ({...prev, [groupId]: response.data}));
    } catch (error) {
      console.error(`Failed to load group feed for ${groupId}:`, error);
    }
  };

  const handleGlobalPhotoCapture = (photoBlob) => {
    setGlobalPhotoFile(photoBlob);
    const photoUrl = URL.createObjectURL(photoBlob);
    setGlobalPhotoPreview(photoUrl);
    setShowGlobalCamera(false);
  };

  const handleGlobalFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setGlobalPhotoFile(file);
      const photoUrl = URL.createObjectURL(file);
      setGlobalPhotoPreview(photoUrl);
    }
  };

  const handleGroupPhotoCapture = (photoBlob) => {
    setGroupPhotoFile(photoBlob);
    const photoUrl = URL.createObjectURL(photoBlob);
    setGroupPhotoPreview(photoUrl);
    setShowGroupCamera(false);
  };

  const handleGroupFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setGroupPhotoFile(file);
      const photoUrl = URL.createObjectURL(file);
      setGroupPhotoPreview(photoUrl);
    }
  };

  const submitGlobalActivity = async () => {
    if (!globalSubmissionText.trim()) {
      alert('Please enter a description of your activity completion');
      return;
    }

    if (!globalPhotoFile) {
      alert('Photo proof is required to complete the activity');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('user_id', user.id);
      formData.append('description', globalSubmissionText.trim());
      formData.append('photo', globalPhotoFile);

      const response = await axios.post(`${API}/daily-global-activity/complete`, formData);
      
      if (response.data.success) {
        alert('Global activity completed! 🎉');
        setGlobalSubmissionText('');
        setGlobalPhotoPreview(null);
        setGlobalPhotoFile(null);
        setShowGlobalSubmission(false);
        // Reload feeds
        await Promise.all([loadGlobalFeed(), loadDailyGlobalActivity()]);
      }
    } catch (error) {
      console.error('Failed to submit global activity:', error);
      alert(error.response?.data?.detail || 'Failed to submit activity');
    }
  };

  const submitGroupActivity = async (groupId) => {
    if (!groupSubmissionText.trim()) {
      alert('Please enter a description of your activity completion');
      return;
    }

    if (!groupPhotoFile) {
      alert('Photo proof is required to complete the group activity');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('user_id', user.id);
      formData.append('description', groupSubmissionText.trim());
      formData.append('photo', groupPhotoFile);

      const response = await axios.post(`${API}/groups/${groupId}/complete-daily-activity`, formData);
      
      if (response.data.success) {
        alert(`Group activity completed! You earned ${response.data.points_earned} points! 🎉`);
        setGroupSubmissionText('');
        setGroupPhotoPreview(null);
        setGroupPhotoFile(null);
        setShowGroupSubmission(null);
        // Reload group feed
        await loadGroupFeed(groupId);
      }
    } catch (error) {
      console.error('Failed to submit group activity:', error);
      alert(error.response?.data?.detail || 'Failed to submit group activity');
    }
  };

  useEffect(() => {
    if (user?.id) {
      Promise.all([
        loadDailyGlobalActivity(),
        loadGlobalFeed(),
        loadUserGroups()
      ]).finally(() => setLoading(false));
    }
  }, [user?.id]);

  const renderFriendsTab = () => {
    return (
      <div className="space-y-6">
        {/* Today's Global Activity - FIXED: Consolidated UI */}
        {dailyGlobalActivity && (
          <div className="bg-gradient-to-r from-purple-600 to-blue-500 text-white p-6 rounded-xl shadow-lg">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h2 className="text-xl font-bold mb-2">🌍 Today's Global Challenge</h2>
                <h3 className="text-lg font-semibold mb-2">{dailyGlobalActivity.activity_title}</h3>
                <p className="text-purple-100 mb-4">{dailyGlobalActivity.activity_description}</p>
                <p className="text-sm opacity-90">
                  {dailyGlobalActivity.participant_count} people participated today
                </p>
              </div>
            </div>

            {/* Dynamic content based on completion status */}
            {globalFeed?.status === 'locked' && (
              <div className="mt-4">
                <div className="flex items-center space-x-2 mb-3">
                  <div className="text-2xl">🔒</div>
                  <div>
                    <p className="font-semibold">Complete First, Then View</p>
                    <p className="text-purple-100 text-sm">Submit your activity to view friends' posts</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowGlobalSubmission(true)}
                  className="bg-white text-purple-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
                >
                  📸 Complete Challenge with Photo
                </button>
              </div>
            )}

            {globalFeed?.status === 'unlocked' && (
              <div className="mt-4">
                <div className="flex items-center space-x-2">
                  <div className="text-2xl">✅</div>
                  <div>
                    <p className="font-semibold">Challenge Completed!</p>
                    <p className="text-purple-100 text-sm">View your friends' posts below</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Global Activity Submission Modal with Photo Upload */}
        {showGlobalSubmission && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Complete Global Activity</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                <strong>{dailyGlobalActivity?.activity_title}</strong>
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    How did you complete this activity?
                  </label>
                  <textarea
                    value={globalSubmissionText}
                    onChange={(e) => setGlobalSubmissionText(e.target.value)}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Describe your completion..."
                    rows="4"
                    maxLength={300}
                  />
                </div>

                {/* Photo Upload Section */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Photo Proof Required *
                  </label>
                  
                  {globalPhotoPreview ? (
                    <div className="space-y-3">
                      <img 
                        src={globalPhotoPreview} 
                        alt="Activity proof" 
                        className="w-full h-48 object-cover rounded-lg"
                      />
                      <button
                        onClick={() => {
                          setGlobalPhotoPreview(null);
                          setGlobalPhotoFile(null);
                        }}
                        className="text-red-600 text-sm hover:text-red-700"
                      >
                        Remove Photo
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex space-x-3">
                        <button
                          onClick={() => setShowGlobalCamera(true)}
                          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          📷 Take Photo
                        </button>
                        <label className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors cursor-pointer text-center">
                          📁 Choose File
                          <input
                            type="file"
                            accept="image/*"
                            onChange={handleGlobalFileSelect}
                            className="hidden"
                          />
                        </label>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Upload a photo showing completion of your activity
                      </p>
                    </div>
                  )}
                </div>
                
                <div className="flex space-x-3">
                  <button
                    onClick={() => {
                      setShowGlobalSubmission(false);
                      setGlobalSubmissionText('');
                      setGlobalPhotoPreview(null);
                      setGlobalPhotoFile(null);
                    }}
                    className="flex-1 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 py-2 px-4 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={submitGlobalActivity}
                    disabled={!globalPhotoFile}
                    className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Submit with Photo
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Group Activity Submission Modal with Photo Upload */}
        {showGroupSubmission && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Complete Group Activity</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                <strong>{groupFeeds[showGroupSubmission]?.activity?.activity_title}</strong>
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {groupFeeds[showGroupSubmission]?.activity?.activity_description}
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    How did you complete this activity?
                  </label>
                  <textarea
                    value={groupSubmissionText}
                    onChange={(e) => setGroupSubmissionText(e.target.value)}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Describe your completion..."
                    rows="4"
                    maxLength={300}
                  />
                </div>

                {/* Photo Upload Section */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Photo Proof Required *
                  </label>
                  
                  {groupPhotoPreview ? (
                    <div className="space-y-3">
                      <img 
                        src={groupPhotoPreview} 
                        alt="Activity proof" 
                        className="w-full h-48 object-cover rounded-lg"
                      />
                      <button
                        onClick={() => {
                          setGroupPhotoPreview(null);
                          setGroupPhotoFile(null);
                        }}
                        className="text-red-600 text-sm hover:text-red-700"
                      >
                        Remove Photo
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex space-x-3">
                        <button
                          onClick={() => setShowGroupCamera(true)}
                          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          📷 Take Photo
                        </button>
                        <label className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors cursor-pointer text-center">
                          📁 Choose File
                          <input
                            type="file"
                            accept="image/*"
                            onChange={handleGroupFileSelect}
                            className="hidden"
                          />
                        </label>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Upload a photo showing completion of your activity
                      </p>
                    </div>
                  )}
                </div>
                
                <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                  <p className="text-sm text-purple-700 dark:text-purple-300">
                    💰 Earn points: 3 for 1st place, 2 for 2nd place, 1 for 3rd+ place
                  </p>
                </div>
                
                <div className="flex space-x-3">
                  <button
                    onClick={() => {
                      setShowGroupSubmission(null);
                      setGroupSubmissionText('');
                      setGroupPhotoPreview(null);
                      setGroupPhotoFile(null);
                    }}
                    className="flex-1 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 py-2 px-4 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => submitGroupActivity(showGroupSubmission)}
                    disabled={!groupPhotoFile}
                    className="flex-1 bg-yellow-600 text-white py-2 px-4 rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Submit with Photo
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Friends Feed - Only show when unlocked */}
        {globalFeed?.status === 'unlocked' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Friends Activity Feed
              </h3>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {globalFeed.friends_count} friends participated
              </span>
            </div>

            {globalFeed.completions && globalFeed.completions.length > 0 ? (
              <div className="space-y-4">
                {globalFeed.completions.map((completion) => (
                  <div key={completion.id} className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
                    <div className="flex items-center mb-3">
                      <div 
                        className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold mr-3"
                        style={{ backgroundColor: '#6366F1' }}
                      >
                        {completion.username?.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-white">
                          {completion.username}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(completion.completed_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    
                    {completion.photo_url && (
                      <img 
                        src={completion.photo_url} 
                        alt="Activity completion"
                        className="w-full h-48 object-cover rounded-lg mb-3"
                      />
                    )}
                    
                    <p className="text-gray-700 dark:text-gray-300">{completion.description}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">👥</div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Friends Yet</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Follow friends to see their activity completions!
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderGroupsTab = () => {
    return (
      <div className="space-y-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Group Activity Feeds
        </h3>

        {userGroups.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">👥</div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Groups Yet</h3>
            <p className="text-gray-600 dark:text-gray-400">
              Join or create a group to see daily activities here
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {userGroups.map((group) => {
              const groupFeed = groupFeeds[group.id];
              
              return (
                <div key={group.id} className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {group.name}
                    </h4>
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {group.member_count} members
                    </span>
                  </div>

                  {groupFeed?.status === 'no_activity' && (
                    <div className="text-center py-6">
                      <div className="text-4xl mb-2">⏰</div>
                      <p className="text-gray-600 dark:text-gray-400">
                        No activity revealed yet for today
                      </p>
                    </div>
                  )}

                  {groupFeed?.status === 'locked' && (
                    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                      <div className="text-center mb-4">
                        <div className="text-4xl mb-2">🔒</div>
                        <h5 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-1">
                          {groupFeed.activity?.activity_title}
                        </h5>
                        <p className="text-yellow-600 dark:text-yellow-300 text-sm mb-4">
                          {groupFeed.activity?.activity_description}
                        </p>
                      </div>
                      <button
                        onClick={() => setShowGroupSubmission(group.id)}
                        className="w-full bg-yellow-600 text-white py-2 px-4 rounded-lg hover:bg-yellow-700 transition-colors"
                      >
                        📸 Complete Group Activity with Photo
                      </button>
                    </div>
                  )}

                  {groupFeed?.status === 'unlocked' && (
                    <div className="space-y-4">
                      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                        <h5 className="font-semibold text-green-800 dark:text-green-200 mb-1">
                          Today's Activity: {groupFeed.activity?.activity_title}
                        </h5>
                        <p className="text-green-600 dark:text-green-300 text-sm">
                          {groupFeed.members_completed} members completed
                        </p>
                      </div>

                      {groupFeed.completions && groupFeed.completions.length > 0 && (
                        <div className="space-y-3">
                          {groupFeed.completions.map((completion) => (
                            <div key={completion.id} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                              <div className="flex items-center mb-2">
                                <div 
                                  className="w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold mr-3 text-sm"
                                  style={{ backgroundColor: completion.user_info?.avatar_color || '#6366F1' }}
                                >
                                  {completion.user_info?.username?.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                  <p className="font-medium text-gray-900 dark:text-white text-sm">
                                    {completion.user_info?.full_name}
                                  </p>
                                  <p className="text-xs text-gray-500 dark:text-gray-400">
                                    {completion.points_earned} points • {new Date(completion.completed_at).toLocaleTimeString()}
                                  </p>
                                </div>
                              </div>
                              
                              {completion.photo_url && (
                                <img 
                                  src={completion.photo_url} 
                                  alt="Activity completion"
                                  className="w-full h-32 object-cover rounded-lg mb-2"
                                />
                              )}
                              
                              {completion.completion_description && (
                                <p className="text-gray-700 dark:text-gray-300 text-sm">
                                  {completion.completion_description}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex space-x-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => setHomeActiveTab('friends')}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
              homeActiveTab === 'friends'
                ? 'bg-white dark:bg-gray-600 text-purple-600 dark:text-purple-400'
                : 'text-gray-600 dark:text-gray-300'
            }`}
          >
            Friends
          </button>
          <button
            onClick={() => setHomeActiveTab('groups')}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
              homeActiveTab === 'groups'
                ? 'bg-white dark:bg-gray-600 text-purple-600 dark:text-purple-400'
                : 'text-gray-600 dark:text-gray-300'
            }`}
          >
            Groups
          </button>
        </div>
      </div>

      <div className="p-4">
        {homeActiveTab === 'friends' && renderFriendsTab()}
        {homeActiveTab === 'groups' && renderGroupsTab()}
      </div>

      {/* Camera Modals */}
      {showGlobalCamera && (
        <CameraCapture 
          onCapture={handleGlobalPhotoCapture}
          onClose={() => setShowGlobalCamera(false)}
        />
      )}

      {showGroupCamera && (
        <CameraCapture 
          onCapture={handleGroupPhotoCapture}
          onClose={() => setShowGroupCamera(false)}
        />
      )}
    </div>
  );
};

// Enhanced GroupsScreen with Weekly Activity Challenge System
const GroupsScreen = ({ user, darkMode }) => {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newGroup, setNewGroup] = useState({ name: '', description: '' });
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [createGroupLoading, setCreateGroupLoading] = useState(false);
  const [createGroupError, setCreateGroupError] = useState('');
  const [createGroupSuccess, setCreateGroupSuccess] = useState('');
  
  // Join group functionality
  const [showJoinForm, setShowJoinForm] = useState(false);
  const [inviteCode, setInviteCode] = useState('');
  const [joinGroupLoading, setJoinGroupLoading] = useState(false);
  const [joinGroupError, setJoinGroupError] = useState('');

  const loadGroups = async () => {
    try {
      const response = await axios.get(`${API}/users/${user.id}/groups`);
      console.log('Groups API response:', response.data);
      setGroups(response.data || []);
    } catch (error) {
      console.error('Failed to load groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const createGroup = async () => {
    if (!newGroup.name.trim()) {
      setCreateGroupError('Please enter a group name');
      return;
    }

    if (newGroup.name.trim().length < 3) {
      setCreateGroupError('Group name must be at least 3 characters long');
      return;
    }

    setCreateGroupLoading(true);
    setCreateGroupError('');

    try {
      const formData = new FormData();
      formData.append('name', newGroup.name.trim());
      formData.append('description', newGroup.description.trim());
      formData.append('category', 'fitness');
      formData.append('is_public', 'false');
      formData.append('user_id', user.id);

      const response = await axios.post(`${API}/groups`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.status === 200) {
        setCreateGroupSuccess('Private group created successfully! 🎉');
        setNewGroup({ name: '', description: '' });
        
        await loadGroups();
        
        setTimeout(() => {
          setShowCreateForm(false);
          setCreateGroupSuccess('');
          setSelectedGroup(response.data);
        }, 1000);
      }
    } catch (error) {
      console.error('Failed to create group:', error);
      setCreateGroupError('Failed to create group. Please try again.');
    } finally {
      setCreateGroupLoading(false);
    }
  };

  const joinGroupByCode = async () => {
    if (!inviteCode.trim()) {
      setJoinGroupError('Please enter an invite code');
      return;
    }

    if (inviteCode.trim().length !== 6) {
      setJoinGroupError('Invite code must be 6 characters long');
      return;
    }

    setJoinGroupLoading(true);
    setJoinGroupError('');
    
    try {
      // Verify user is authenticated
      if (!user || !user.id) {
        setJoinGroupError('User authentication required. Please log in again.');
        return;
      }

      const formData = new FormData();
      formData.append('invite_code', inviteCode.trim().toUpperCase());
      formData.append('user_id', user.id);

      console.log('Joining group with code:', inviteCode.trim().toUpperCase());
      console.log('User ID:', user.id);

      const response = await axios.post(`${API}/groups/join-by-code`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      console.log('Join group response:', response.data);
      
      if (response.data.success) {
        alert('Successfully joined group! 🎉');
        setInviteCode('');
        setShowJoinForm(false);
        setJoinGroupError('');
        await loadGroups();
      } else {
        setJoinGroupError(response.data.message || 'Failed to join group');
      }
    } catch (error) {
      console.error('Failed to join group:', error);
      console.error('Error details:', error.response?.data);
      
      let errorMessage = 'Failed to join group';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setJoinGroupError(errorMessage);
    } finally {
      setJoinGroupLoading(false);
    }
  };

  useEffect(() => {
    loadGroups();
  }, [user.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (selectedGroup) {
    return (
      <WeeklyActivityGroupScreen 
        group={selectedGroup} 
        user={user} 
        onBack={() => setSelectedGroup(null)}
        darkMode={darkMode}
      />
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Weekly Challenge Groups</h1>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowJoinForm(true)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors text-sm"
            >
              Join Group
            </button>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors text-sm"
            >
              Create Group
            </button>
          </div>
        </div>
      </div>

      {/* Join Group Modal - FIXED: Enhanced error handling */}
      {showJoinForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Join Group</h2>
            
            {joinGroupError && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                {joinGroupError}
              </div>
            )}
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Invite Code
                </label>
                <input
                  type="text"
                  value={inviteCode}
                  onChange={(e) => {
                    setInviteCode(e.target.value.toUpperCase());
                    setJoinGroupError(''); // Clear error when typing
                  }}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white uppercase"
                  placeholder="Enter 6-digit code"
                  maxLength={6}
                />
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setShowJoinForm(false);
                    setInviteCode('');
                    setJoinGroupError('');
                  }}
                  className="flex-1 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 py-2 px-4 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500"
                  disabled={joinGroupLoading}
                >
                  Cancel
                </button>
                <button
                  onClick={joinGroupByCode}
                  disabled={joinGroupLoading || !inviteCode.trim()}
                  className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {joinGroupLoading ? 'Joining...' : 'Join Group'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Group Form */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Create Weekly Challenge Group</h2>
            
            {createGroupSuccess && (
              <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                {createGroupSuccess}
              </div>
            )}

            {createGroupError && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                {createGroupError}
              </div>
            )}
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Group Name *
                </label>
                <input
                  type="text"
                  value={newGroup.name}
                  onChange={(e) => {
                    setNewGroup({...newGroup, name: e.target.value});
                    setCreateGroupError('');
                  }}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Enter group name"
                  maxLength={50}
                  disabled={createGroupLoading}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  value={newGroup.description}
                  onChange={(e) => setNewGroup({...newGroup, description: e.target.value})}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Describe your group"
                  rows="3"
                  maxLength={200}
                  disabled={createGroupLoading}
                />
              </div>
              
              <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                <p className="text-sm text-purple-700 dark:text-purple-300">
                  🏆 Weekly Challenge Group: Submit 7 activities together, compete daily for points!
                </p>
                <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                  Maximum 7 members • Private group with invite code
                </p>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewGroup({ name: '', description: '' });
                    setCreateGroupError('');
                    setCreateGroupSuccess('');
                  }}
                  className="flex-1 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 py-2 px-4 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 disabled:opacity-50"
                  disabled={createGroupLoading}
                >
                  Cancel
                </button>
                <button
                  onClick={createGroup}
                  disabled={createGroupLoading || !newGroup.name.trim()}
                  className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {createGroupLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Creating...
                    </>
                  ) : (
                    'Create Group'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Groups List */}
      <div className="p-4">
        {groups.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🏆</div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Groups Yet</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Create or join a weekly challenge group to compete with friends!
            </p>
            <div className="space-y-3">
              <button
                onClick={() => setShowCreateForm(true)}
                className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors"
              >
                Create Your First Group
              </button>
              <div className="text-sm text-gray-500">or</div>
              <button
                onClick={() => setShowJoinForm(true)}
                className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors"
              >
                Join with Invite Code
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {groups.map((group) => (
              <div key={group.id} className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-lg border border-gray-200 dark:border-gray-700">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {group.name}
                      </h3>
                      {group.admin_id === user.id && (
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">ADMIN</span>
                      )}
                    </div>
                    
                    {group.description && (
                      <p className="text-gray-600 dark:text-gray-400 text-sm mb-3">
                        {group.description}
                      </p>
                    )}
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400 mb-3">
                      <span>👥 {group.member_count}/{group.max_members} members</span>
                      <span>📅 Created {new Date(group.created_at).toLocaleDateString()}</span>
                    </div>

                    {/* Weekly Progress */}
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 mb-3">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">This Week's Progress</span>
                        <span className="text-sm text-purple-600 dark:text-purple-400">
                          {group.activities_submitted_this_week || 0}/7 activities
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                        <div 
                          className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${((group.activities_submitted_this_week || 0) / 7) * 100}%` }}
                        ></div>
                      </div>
                      
                      {group.submission_phase_active && (
                        <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                          🟢 Submission phase active
                        </p>
                      )}
                    </div>

                    {/* Invite Code */}
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-2 mb-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-blue-700 dark:text-blue-300">Invite Code:</span>
                        <span className="text-sm font-mono font-bold text-blue-800 dark:text-blue-200">
                          {group.invite_code}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => setSelectedGroup(group)}
                    className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors text-sm ml-4"
                  >
                    Enter Group
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Weekly Activity Group Screen - Main group interface
const WeeklyActivityGroupScreen = ({ group, user, onBack, darkMode }) => {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [weeklyActivities, setWeeklyActivities] = useState([]);
  const [currentDayActivity, setCurrentDayActivity] = useState(null);
  const [rankings, setRankings] = useState([]);
  
  // Activity submission state
  const [showSubmitForm, setShowSubmitForm] = useState(false);
  const [activityTitle, setActivityTitle] = useState('');
  const [activityDescription, setActivityDescription] = useState('');
  const [submitLoading, setSubmitLoading] = useState(false);

  // Admin functions state
  const [submissionDay, setSubmissionDay] = useState(group.submission_day || '');
  const [showAdminPanel, setShowAdminPanel] = useState(false);

  const isAdmin = group.admin_id === user.id;

  const loadGroupData = async () => {
    try {
      const [activitiesRes, currentActivityRes, rankingsRes] = await Promise.all([
        axios.get(`${API}/groups/${group.id}/weekly-activities`),
        axios.get(`${API}/groups/${group.id}/current-day-activity`),
        axios.get(`${API}/groups/${group.id}/weekly-rankings`)
      ]);
      
      console.log('Weekly activities loaded:', activitiesRes.data);
      setWeeklyActivities(activitiesRes.data || []);
      setCurrentDayActivity(currentActivityRes.data?.activity);
      setRankings(rankingsRes.data?.rankings || []);
    } catch (error) {
      console.error('Failed to load group data:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitActivity = async () => {
    if (!activityTitle.trim() || !activityDescription.trim()) {
      alert('Please fill in both title and description');
      return;
    }

    setSubmitLoading(true);
    try {
      const formData = new FormData();
      formData.append('activity_title', activityTitle.trim());
      formData.append('activity_description', activityDescription.trim());
      formData.append('user_id', user.id);

      console.log('Submitting activity to:', `${API}/groups/${group.id}/submit-activity`);
      const response = await axios.post(`${API}/groups/${group.id}/submit-activity`, formData);
      
      console.log('Activity submission response:', response.data);
      
      if (response.data.success) {
        alert(`Activity submitted! ${response.data.remaining} more needed.`);
        setActivityTitle('');
        setActivityDescription('');
        setShowSubmitForm(false);
        await loadGroupData(); // Reload data to show new activity
      }
    } catch (error) {
      console.error('Failed to submit activity:', error);
      console.error('Error details:', error.response?.data);
      alert(error.response?.data?.detail || 'Failed to submit activity');
    } finally {
      setSubmitLoading(false);
    }
  };

  const startWeeklySubmissions = async () => {
    try {
      const formData = new FormData();
      formData.append('admin_id', user.id);

      const response = await axios.post(`${API}/groups/${group.id}/start-weekly-submissions`, formData);
      
      if (response.data.success) {
        alert('Weekly submission phase started! 🎉');
        // Reload the group data to reflect the updated submission_phase_active status
        window.location.reload(); // Force a reload to get updated group data
      }
    } catch (error) {
      console.error('Failed to start submissions:', error);
      alert(error.response?.data?.detail || 'Failed to start submissions');
    }
  };

  const setSubmissionDayAdmin = async () => {
    if (!submissionDay) {
      alert('Please select a submission day');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('submission_day', submissionDay);
      formData.append('admin_id', user.id);

      const response = await axios.post(`${API}/groups/${group.id}/set-submission-day`, formData);
      
      if (response.data.success) {
        alert(`Submission day set to ${submissionDay}! 📅`);
        setShowAdminPanel(false);
      }
    } catch (error) {
      console.error('Failed to set submission day:', error);
      alert(error.response?.data?.detail || 'Failed to set submission day');
    }
  };

  // FIXED: Added the missing revealDailyActivity function
  const revealDailyActivity = async () => {
    if (!isAdmin) {
      alert('Only group admin can reveal daily activities');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('admin_id', user.id);
      formData.append('day_number', 1); // You might want to track this properly

      const response = await axios.post(`${API}/groups/${group.id}/reveal-daily-activity`, formData);
      
      if (response.data.success) {
        alert(`Activity revealed: ${response.data.revealed_activity.activity_title} 🎉`);
        await loadGroupData(); // Reload to show the revealed activity
        setShowAdminPanel(false);
      }
    } catch (error) {
      console.error('Failed to reveal activity:', error);
      alert(error.response?.data?.detail || 'Failed to reveal activity');
    }
  };

  useEffect(() => {
    loadGroupData();
  }, [group.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center mb-4">
          <button
            onClick={onBack}
            className="mr-3 text-purple-600 hover:text-purple-700"
          >
            ← Back
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">{group.name}</h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              👥 {group.member_count} members • 📊 Weekly Challenge Group
            </p>
          </div>
          {isAdmin && (
            <button
              onClick={() => setShowAdminPanel(true)}
              className="bg-orange-600 text-white px-3 py-1 rounded text-xs hover:bg-orange-700"
            >
              Admin
            </button>
          )}
        </div>
        
        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'overview'
                ? 'bg-white dark:bg-gray-600 text-purple-600 dark:text-purple-400'
                : 'text-gray-600 dark:text-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('activities')}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'activities'
                ? 'bg-white dark:bg-gray-600 text-purple-600 dark:text-purple-400'
                : 'text-gray-600 dark:text-gray-300'
            }`}
          >
            Activities ({weeklyActivities.length}/7)
          </button>
          <button
            onClick={() => setActiveTab('rankings')}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'rankings'
                ? 'bg-white dark:bg-gray-600 text-purple-600 dark:text-purple-400'
                : 'text-gray-600 dark:text-gray-300'
            }`}
          >
            Rankings
          </button>
        </div>
      </div>

      {/* Admin Panel Modal */}
      {showAdminPanel && isAdmin && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Admin Panel</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Weekly Submission Day
                </label>
                <select
                  value={submissionDay}
                  onChange={(e) => setSubmissionDay(e.target.value)}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">Choose day...</option>
                  <option value="Monday">Monday</option>
                  <option value="Tuesday">Tuesday</option>
                  <option value="Wednesday">Wednesday</option>
                  <option value="Thursday">Thursday</option>
                  <option value="Friday">Friday</option>
                  <option value="Saturday">Saturday</option>
                  <option value="Sunday">Sunday</option>
                </select>
              </div>

              <button
                onClick={setSubmissionDayAdmin}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
              >
                Set Submission Day
              </button>

              <button
                onClick={startWeeklySubmissions}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700"
              >
                Start Weekly Submissions
              </button>

              <button
                onClick={() => revealDailyActivity()}
                className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700"
              >
                Reveal Today's Activity
              </button>

              <button
                onClick={() => setShowAdminPanel(false)}
                className="w-full bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 py-2 px-4 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Activity Submission Modal */}
      {showSubmitForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Submit Activity Idea</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Activity Title *
                </label>
                <input
                  type="text"
                  value={activityTitle}
                  onChange={(e) => setActivityTitle(e.target.value)}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="e.g., 20 Push-ups Challenge"
                  maxLength={100}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Description *
                </label>
                <textarea
                  value={activityDescription}
                  onChange={(e) => setActivityDescription(e.target.value)}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Describe the activity and how to do it..."
                  rows="4"
                  maxLength={300}
                />
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setShowSubmitForm(false);
                    setActivityTitle('');
                    setActivityDescription('');
                  }}
                  className="flex-1 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 py-2 px-4 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500"
                >
                  Cancel
                </button>
                <button
                  onClick={submitActivity}
                  disabled={submitLoading}
                  className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 disabled:opacity-50"
                >
                  {submitLoading ? 'Submitting...' : 'Submit'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Content */}
      <div className="p-4">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Current Week Status */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">This Week's Challenge</h3>
              
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Activity Submissions</span>
                  <span className="text-sm text-purple-600 dark:text-purple-400">
                    {weeklyActivities.length}/7 submitted
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                  <div 
                    className="bg-purple-600 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${(weeklyActivities.length / 7) * 100}%` }}
                  ></div>
                </div>
              </div>

              {group.submission_phase_active && weeklyActivities.length < 7 && (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="text-green-800 dark:text-green-200 font-medium">🎯 Submission Phase Active!</p>
                      <p className="text-green-600 dark:text-green-300 text-sm">
                        Your group needs {7 - weeklyActivities.length} more activity ideas to start the challenge
                      </p>
                    </div>
                    <button
                      onClick={() => setShowSubmitForm(true)}
                      className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                    >
                      Submit Activity Idea
                    </button>
                  </div>
                  
                  {/* Show submission tips */}
                  <div className="bg-green-100 dark:bg-green-800/20 rounded-lg p-3 mt-3">
                    <p className="text-green-700 dark:text-green-300 text-sm font-medium mb-2">💡 Submission Tips:</p>
                    <ul className="text-green-600 dark:text-green-400 text-xs space-y-1">
                      <li>• Any member can submit activities (flexible distribution)</li>
                      <li>• Ideas should be achievable by all group members</li>
                      <li>• Once 7 activities are submitted, daily reveals begin!</li>
                      <li>• Examples: "20 push-ups", "10-minute walk", "yoga session"</li>
                    </ul>
                  </div>
                </div>
              )}

              {!group.submission_phase_active && weeklyActivities.length === 0 && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                  <p className="text-yellow-800 dark:text-yellow-200 font-medium">Waiting for Admin</p>
                  <p className="text-yellow-600 dark:text-yellow-300 text-sm">
                    The group admin needs to start the weekly submission phase
                  </p>
                </div>
              )}

              {weeklyActivities.length === 7 && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <p className="text-blue-800 dark:text-blue-200 font-medium">Ready for Daily Challenges! 🎉</p>
                  <p className="text-blue-600 dark:text-blue-300 text-sm">
                    All 7 activities submitted. Daily reveals will begin soon!
                  </p>
                </div>
              )}
            </div>

            {/* Today's Activity */}
            {currentDayActivity && (
              <div className="bg-gradient-to-r from-purple-600 to-blue-500 text-white rounded-xl p-6 shadow-lg">
                <h3 className="text-lg font-bold mb-2">Today's Challenge 🏆</h3>
                <h4 className="text-xl font-semibold mb-2">{currentDayActivity.activity_title}</h4>
                <p className="text-purple-100 mb-4">{currentDayActivity.activity_description}</p>
                <button className="bg-white text-purple-600 px-6 py-2 rounded-lg font-semibold hover:bg-gray-100">
                  Complete Challenge
                </button>
              </div>
            )}

            {/* Group Members */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Group Members ({group.member_count}/{group.max_members})
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {rankings.map((member) => (
                  <div key={member.user_id} className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div 
                      className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold"
                      style={{ backgroundColor: member.avatar_color }}
                    >
                      {member.username.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-white">{member.full_name}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{member.points} points</p>
                    </div>
                    {group.admin_id === member.user_id && (
                      <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">ADMIN</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'activities' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Weekly Activities ({weeklyActivities.length}/7)
              </h3>
              {group.submission_phase_active && weeklyActivities.length < 7 && (
                <button
                  onClick={() => setShowSubmitForm(true)}
                  className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                >
                  Submit Activity
                </button>
              )}
            </div>

            {weeklyActivities.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📝</div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Activities Yet</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Group needs to submit 7 activity ideas to start the weekly challenge
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {weeklyActivities.map((activity, index) => (
                  <div key={activity.id} className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-lg">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-sm bg-purple-100 text-purple-700 px-2 py-1 rounded">
                            #{activity.submission_order}
                          </span>
                          <h4 className="font-semibold text-gray-900 dark:text-white">
                            {activity.activity_title}
                          </h4>
                        </div>
                        <p className="text-gray-600 dark:text-gray-400 text-sm mb-2">
                          {activity.activity_description}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-500">
                          Submitted {new Date(activity.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      {activity.is_revealed && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                          REVEALED
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'rankings' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Weekly Rankings</h3>
            
            {rankings.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🏆</div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Rankings Yet</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Complete daily activities to earn points and climb the leaderboard!
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {rankings.map((member, index) => (
                  <div key={member.user_id} className={`bg-white dark:bg-gray-800 rounded-xl p-4 shadow-lg ${
                    index === 0 ? 'border-2 border-yellow-400' : 
                    index === 1 ? 'border-2 border-gray-400' : 
                    index === 2 ? 'border-2 border-amber-600' : ''
                  }`}>
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl">
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}
                      </div>
                      <div 
                        className="w-12 h-12 rounded-full flex items-center justify-center text-white font-semibold"
                        style={{ backgroundColor: member.avatar_color }}
                      >
                        {member.username.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900 dark:text-white">{member.full_name}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">@{member.username}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{member.points}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">points</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = ({ activeTab, setActiveTab, notifications, onPhotoClick, darkMode }) => {
  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-4 py-2">
      <div className="flex justify-around">
        {[
          { id: 'feed', icon: '🏠', label: 'Home' },
          { id: 'groups', icon: '👥', label: 'Groups' },
          { id: 'photo', icon: '📸', label: 'Photo' },
          { id: 'notifications', icon: '🔔', label: 'Notifications' },
          { id: 'profile', icon: '👤', label: 'Profile' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => tab.id === 'photo' ? onPhotoClick() : setActiveTab(tab.id)}
            className={`flex flex-col items-center p-2 rounded-lg transition-all duration-200 ${
              activeTab === tab.id
                ? 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20' 
                : 'text-gray-600 dark:text-gray-400'
            } hover:bg-gray-100 dark:hover:bg-gray-700`}
          >
            <div className="relative">
              <span className="text-xl">{tab.icon}</span>
              {tab.id === 'notifications' && unreadCount > 0 && (
                <div className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </div>
              )}
            </div>
            <span className="text-xs mt-1">{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

// Simple NotificationsScreen
const NotificationsScreen = ({ user, notifications, setNotifications, onNavigate }) => {
  return (
    <div className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">Notifications</h1>
      </div>

      <div className="p-4">
        {notifications.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔔</div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No notifications yet</h2>
            <p className="text-gray-600 dark:text-gray-400">
              You'll see updates about challenges and activities here
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className="bg-white dark:bg-gray-800 p-4 rounded-xl"
              >
                <p className="font-medium text-gray-900 dark:text-white">
                  {notification.title}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                  {notification.message}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Simple ProfileScreen 
const ProfileScreen = ({ user, onLogout, darkMode, setDarkMode }) => {
  return (
    <div className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">Profile</h1>
      </div>

      <div className="p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
          <div className="flex items-center mb-4">
            <div 
              className="w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-bold mr-4"
              style={{ backgroundColor: user.avatar_color }}
            >
              {user.username.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">{user.full_name}</h2>
              <p className="text-gray-600 dark:text-gray-400">@{user.username}</p>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              {darkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
            </button>
            <button
              onClick={onLogout}
              className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('feed');
  const [showCamera, setShowCamera] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [notifications, setNotifications] = useState([]);

  // Initialize user and load data
  useEffect(() => {
    const initializeApp = async () => {
      const storedUser = localStorage.getItem('actify_user');
      const storedSession = localStorage.getItem('actify_session');
      const authTimestamp = localStorage.getItem('actify_auth_timestamp');
      
      if (storedUser && storedSession && authTimestamp) {
        try {
          const userData = JSON.parse(storedUser);
          const sessionAge = Date.now() - parseInt(authTimestamp);
          
          if (sessionAge < 24 * 60 * 60 * 1000) {
            setUser(userData);
            console.log('Session restored for user:', userData.username);
          }
        } catch (error) {
          console.error('Failed to restore session:', error);
          handleLogout();
        }
      }
    };

    initializeApp();
  }, []);

  const handleLogin = (newUser) => {
    setUser(newUser);
    localStorage.setItem('actify_user', JSON.stringify(newUser));
    localStorage.setItem('actify_auth_timestamp', new Date().getTime().toString());
  };

  const handleLogout = () => {
    setUser(null);
    setActiveTab('feed');
    setNotifications([]);
    localStorage.removeItem('actify_user');
    localStorage.removeItem('actify_session');
    localStorage.removeItem('actify_auth_timestamp');
  };

  if (!user) {
    return <AuthScreen onLogin={handleLogin} darkMode={darkMode} />;
  }

  return (
    <div className={`${darkMode ? 'dark' : ''} bg-gray-50 dark:bg-gray-900`}>
      <div className="min-h-screen flex flex-col max-w-md mx-auto bg-white dark:bg-gray-900 shadow-lg">
        <div className="flex-1 overflow-hidden">
          {activeTab === 'feed' && <FeedScreen user={user} />}
          {activeTab === 'groups' && <GroupsScreen user={user} darkMode={darkMode} />}
          {activeTab === 'notifications' && <NotificationsScreen user={user} notifications={notifications} setNotifications={setNotifications} />}
          {activeTab === 'profile' && <ProfileScreen user={user} onLogout={handleLogout} darkMode={darkMode} setDarkMode={setDarkMode} />}
        </div>
        
        <Navigation 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
          notifications={notifications}
          onPhotoClick={() => setShowCamera(true)}
          darkMode={darkMode}
        />
      </div>

      {showCamera && (
        <CameraCapture 
          onCapture={(blob) => {
            console.log('Photo captured:', blob);
            setShowCamera(false);
          }}
          onClose={() => setShowCamera(false)}
          darkMode={darkMode}
        />
      )}
    </div>
  );
};

export default App;