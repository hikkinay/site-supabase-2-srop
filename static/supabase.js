import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

export const supabase = createClient(
    "https://nvvnnmcoyopyjwhdbpkr.supabase.co",   // ← Project URL
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52dm5ubWNveW9weWp3aGRicGtyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzNzA2OTIsImV4cCI6MjA3Nzk0NjY5Mn0.4s0YucPF25sQKjUBjVK0KWF6T4qz5soAva1LKdGkgZE"                          // ← anon public key
);
