import axios from "axios";
import { supabase } from "./supabaseClient";

const api = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL || "https://your-backend-domain.com",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;
