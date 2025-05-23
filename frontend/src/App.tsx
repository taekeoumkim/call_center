import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ClientPage from './pages/ClientPage';
import AuthPage from './pages/AuthPage';
import MainPage from './pages/MainPage';
import ClientDetailPage from './pages/ClientDetailPage';
import MyPage from './pages/MyPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path='/' element={<AuthPage />} />
        <Route path='/client' element={<ClientPage />} />
        <Route path='/main' element={<MainPage />} />
        <Route path='/patient/:id' element={<ClientDetailPage />} />
        <Route path='/mypage' element={<MyPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
