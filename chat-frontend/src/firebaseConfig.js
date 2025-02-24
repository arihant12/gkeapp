// ✅ Import Firebase Modules
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth";

// ✅ Firebase Configuration (Replace with actual values)
const firebaseConfig = {
  apiKey: "AIzaSyDsxErqANu39_AtR3DFypENlfmlx4tK95Y",
  authDomain: "uni-connect-446707.firebaseapp.com",
  projectId: "uni-connect-446707",
  storageBucket: "uni-connect-446707.firebasestorage.app",
  messagingSenderId: "535506613508",
  appId: "1:535506613508:web:6749f8a36ed0c9334f4c51",
  measurementId: "G-H5KQWEGY0Q"
};

// ✅ Initialize Firebase
const firebaseApp = initializeApp(firebaseConfig);
const auth = getAuth(firebaseApp);
const provider = new GoogleAuthProvider();

export { auth, provider, signInWithPopup };
