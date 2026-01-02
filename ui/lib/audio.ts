/**
 * Audio utility functions for formatting and handling audio-related data.
 */

/**
 * Format seconds to MM:SS format
 */
export function formatTime(seconds: number): string {
  if (isNaN(seconds) || !isFinite(seconds)) {
    return "00:00";
  }
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

/**
 * Get audio URL for a conversation
 */
export function getAudioUrl(conversationId: string): string {
  return `/api/audio/${conversationId}`;
}

/**
 * Playback speed options
 */
export const PLAYBACK_SPEEDS = [0.5, 1, 1.5, 2] as const;

export type PlaybackSpeed = (typeof PLAYBACK_SPEEDS)[number];
