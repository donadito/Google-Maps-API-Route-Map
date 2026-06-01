import React, { useState } from 'react';
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "../services/firebase"; // Importamos tu "Portero"

interface LoginProps {
  onLoginSuccess: (user: any) => void;
}

const Login = ({ onLoginSuccess }: LoginProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); 
    setError('');

    try {
      // Intentamos abrir la puerta con las llaves del usuario
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;
      
      console.log("¡Bienvenido, dhakita!", user.email);
      onLoginSuccess(user); // Avisamos al resto de la app que ya entramos
    } catch (err: any) {
      // Si las llaves no funcionan, mostramos un mensaje
      setError("Correo o contraseña incorrectos. Inténtalo de nuevo. Nota que las únicas personas con acceso son los propietarios del proyecto.");
      console.error(err.code, err.message);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: 'auto', padding: '20px' }}>
      <h2>Iniciar Sesión</h2>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '10px' }}>
          <label>Correo electrónico:</label>
          <input 
            type="email" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            required 
            style={{ width: '100%', padding: '8px' }}
          />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label>Contraseña:</label>
          <input 
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            required 
            style={{ width: '100%', padding: '8px' }}
          />
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" style={{ width: '100%', padding: '10px', cursor: 'pointer' }}>
          Entrar
        </button>
      </form>
    </div>
  );
};

export default Login;