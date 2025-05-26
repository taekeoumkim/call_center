// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import MainPage from './pages/MainPage';
import { AuthProvider, useAuth } from './context/AuthContext';

// 로그인이 필요한 라우트를 감싸는 컴포넌트
const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return <div>Checking authentication...</div>; // 또는 스피너
  }
  return isAuthenticated ? <Outlet /> : <Navigate to="/auth" replace />;
};

// 로그인이 되어있으면 대시보드로, 아니면 인증 페이지로 보내는 컴포넌트
const PublicRoute: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div>Checking authentication...</div>;
  return isAuthenticated ? <Navigate to="/main" replace /> : <Outlet />;
};


function AppContent() { // 라우트 부분을 별도 컴포넌트로 분리 (useAuth를 Provider 내부에서 사용하기 위함)
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="flex justify-center items-center min-h-screen">Loading App...</div>;
  }

  return (
    <Routes>
      <Route element={<PublicRoute />}>
        <Route path="/auth" element={<AuthPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route path="/main" element={<MainPage />} />
        {/* <Route path="/dashboard" element={<Navigate to="/main" replace />} /> */} {/* dashboard 대신 main 사용 */}
        {/* 다른 보호된 라우트들 추가 */}
      </Route>

      <Route
        path="/"
        element={
          isAuthenticated ? (
            <Navigate to="/main" replace />
          ) : (
            <Navigate to="/auth" replace />
          )
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}


function App() {
  return (
    <Router>
      <AuthProvider> {/* AuthProvider로 AppContent를 감싸줌 */}
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;