/**
 * ============================================================================
 * UUID Service
 * ============================================================================
 * Utility service for generating UUIDs.
 * 
 * Follows Single Responsibility Principle:
 * - Only handles UUID generation
 * - Extracted from components for reusability
 * - Easy to test and mock
 */

import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class UuidService {
  /**
   * Generate a RFC4122 version 4 compliant UUID.
   * 
   * How it works:
   * 1. Template: 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
   * 2. Replace each 'x' and 'y' with random hex digits
   * 3. '4' indicates version 4 (random)
   * 4. 'y' becomes 8, 9, a, or b (variant bits)
   * 
   * @returns A new UUID string
   */
  generate(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  /**
   * Validate if a string is a valid UUID format.
   * 
   * @param uuid - String to validate
   * @returns True if valid UUID format
   */
  isValid(uuid: string): boolean {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(uuid);
  }
}
