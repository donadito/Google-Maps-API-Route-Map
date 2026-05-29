import './App.css'
import { useState, useEffect } from 'react'
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom'
import { onAuthStateChanged, User } from 'firebase/auth'
import { auth } from './services/firebase' // Tu portero
import RouteOptimizerPage from './pages/RouteOptimizerPage'
import Login from './components/Login' // Tu formulario

function App() {
  const [usuario, setUsuario] = useState<User | null>(null);
  const [cargando, setCargando] = useState(true);

  // El vigilante de Firebase que revisa si hay sesión activa
  useEffect(() => {
    const desescribirVigilante = onAuthStateChanged(auth, (usuarioDetectado) => {
      setUsuario(usuarioDetectado ? usuarioDetectado : null);
      setCargando(false);
    });

    return () => desescribirVigilante();
  }, []);

  if (cargando) {
    return (
      <div style={{ display: 'grid', placeItems: 'center', height: '100vh', fontFamily: 'sans-serif', color: '#0f6c7a' }}>
        <h3>Cargando credenciales de seguridad...</h3>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* RUTA DEL LOGIN */}
        <Route 
          path="/login" 
          element={usuario ? <Navigate to="/" replace /> : <Login onLoginSuccess={(u) => setUsuario(u)} />} 
        />

        {/* RUTA PRINCIPAL PROTEGIDA */}
        <Route 
          path="/" 
          element={usuario ? <RouteOptimizerPage /> : <Navigate to="/login" replace />} 
        />

        {/* Ruta comodín por si escriben cualquier otra cosa, redirige al inicio */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App