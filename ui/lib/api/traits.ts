/**
 * Traits API client.
 */

import { BaseApiClient } from "./base";
import type { TraitVocabularyResponse } from "../types";

export class TraitsApi extends BaseApiClient {
  /**
   * Get the trait vocabulary.
   */
  async getTraitVocabulary(): Promise<TraitVocabularyResponse> {
    return this.get<TraitVocabularyResponse>("/api/v1/traits");
  }
}
