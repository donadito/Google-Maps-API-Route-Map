// @ts-ignore
import './App.css'
import { useState, useEffect } from 'react'

import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom'
import { onAuthStateChanged } from 'firebase/auth'
import { auth } from './services/firebase' // Tu portero
import RouteOptimizerPage from './pages/RouteOptimizerPage'
import Login from './components/Login' // Tu formulario

function App() {
  // Dejamos que TypeScript infiera el estado automáticamente (acepta null o el objeto de usuario)
  const [usuario, setUsuario] = useState<any>(null);
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
        {/* 1. RUTA DEL LOGIN: Aquí es donde debes poner el (u: any) */}
        <Route 
          path="/login" 
          element={usuario ? <Navigate to="/" replace /> : <Login onLoginSuccess={(u: any) => setUsuario(u)} />} 
        />

        {/* 2. RUTA PRINCIPAL PROTEGIDA: Aquí NO necesitas el componente Login, solo la página del optimizador */}
        <Route 
          path="/" 
          element={usuario ? <RouteOptimizerPage /> : <Navigate to="/login" replace />} 
        />

        {/* 3. RUTA COMODÍN */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App