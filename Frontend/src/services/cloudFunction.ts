// @ts-nocheck
import { auth } from "./firebase"; // Traemos al "portero" que ya configuramos

/**
 * Función para enviar los destinos al backend de Python (Cloud Function)
 * @param {Array} destinos - Lista de hasta 15 destinos elegidos por el usuario
 * @param {string} modoCalculo - Puede ser 'abierta' o 'cerrada'
 */
export const optimizarRutaConBackend = async (destinos, modoCalculo) => {
  try {
    // 1. Revisamos si hay un usuario con la sesión iniciada en la app
    const usuarioActual = auth.currentUser;

    if (!usuarioActual) {
      throw new Error("No hay ningún usuario autenticado. Inicia sesión primero.");
    }

    // 2. Le pedimos a Firebase su "brazalete VIP" (ID Token) actualizado
    const idToken = await usuarioActual.getIdToken();

    // 3. Obtenemos la URL de la Cloud Function desde nuestras variables de entorno
    const urlBackend = import.meta.env.VITE_API_BASE_URL;

    // 4. Hacemos la llamada (Fetch) enviando el token en los encabezados (Headers)
    const respuesta = await fetch(`${urlBackend}/optimizar`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Aquí le mostramos el token de seguridad al guardia del backend
        "Authorization": `Bearer ${idToken}`
      },
      body: JSON.stringify({
        destinos: destinos,          // Entre 2 y 15 destinos
        modo: modoCalculo            // Ruta abierta o cerrada
      })
    });

    // 5. Si el backend nos rechaza (por token inválido o IP bloqueada), lanzamos un error
    if (!respuesta.ok) {
      throw new Error(`Error en el servidor: ${respuesta.status}`);
    }

    // 6. Si todo sale bien, recibimos la ruta ordenada y la distancia total
    const resultado = await respuesta.json();
    return resultado; 

  } catch (error) {
    console.error("Error en la petición de optimización:", error);
    throw error;
  }
};