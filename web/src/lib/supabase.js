import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export const supabase = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null

/**
 * Save a generation record to Supabase.
 * Silently skips if Supabase is not configured.
 */
export async function saveGeneration({ videoUrl, metadata }) {
  if (!supabase) {
    console.warn('Supabase not configured — skipping save.')
    return null
  }

  const { data, error } = await supabase
    .from('generations')
    .insert([
      {
        video_url: videoUrl,
        metadata,
      },
    ])
    .select()

  if (error) {
    console.error('Failed to save generation:', error)
    return null
  }

  return data?.[0] ?? null
}
