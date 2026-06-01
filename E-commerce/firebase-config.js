import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyDM1aX1N4UQVhhl1RGn_tAXrAxh9mtjZY4",
  authDomain: "ecommerce-74d5c.firebaseapp.com",
  projectId: "ecommerce-74d5c",
  storageBucket: "ecommerce-74d5c.firebasestorage.app",
  messagingSenderId: "976986068176",
  appId: "1:976986068176:web:a8bfb567107e823eb7fad5",
  measurementId: "G-QQENVYKVZH"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export { auth };
export default firebaseConfig;