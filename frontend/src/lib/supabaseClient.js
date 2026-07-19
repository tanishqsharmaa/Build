/**
 * Supabase JS client — anon key, safe for client-side use (RLS enforces security).
 * Used in client-side Svelte components only (not in +page.server.js).
 * Server-side loads use the service key via $env/dynamic/private + @supabase/supabase-js directly.
 *
 * Requires PUBLIC_SUPABASE_URL and PUBLIC_SUPABASE_ANON_KEY in .env.local
 * (or equivalent PUBLIC_ vars in production).
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl  = import.meta.env.VITE_SUPABASE_URL  ?? '';
const supabaseAnon = import.meta.env.VITE_SUPABASE_ANON_KEY ?? '';

if (!supabaseUrl || !supabaseAnon) {
  console.warn('[supabaseClient] VITE_SUPABASE_URL or VITE_SUPABASE_ANON not set — Supabase client is non-functional.');
}

export const supabase = createClient(supabaseUrl, supabaseAnon);
