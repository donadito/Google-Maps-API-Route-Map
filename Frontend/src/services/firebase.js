import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

// Llaves restringidas
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};

// Inicializacion de Firebase
const app = initializeApp(firebaseConfig);

// Exportacion del "Portero" (auth) para usarlo en el Login
export const auth = getAuth(app);