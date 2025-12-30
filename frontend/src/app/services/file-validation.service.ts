/**
 * ============================================================================
 * File Validation Service
 * ============================================================================
 * Centralized file validation following Single Responsibility Principle.
 * 
 * Benefits:
 * - Reusable validation logic
 * - Configuration from environment
 * - Easy to test
 * - Consistent validation across components
 */

import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export interface FileValidationConfig {
  allowedExtensions: string[];
  maxPdfSizeBytes: number;
  maxImageSizeBytes: number;
  maxFileSizeBytes: number;
}

@Injectable({
  providedIn: 'root'
})
export class FileValidationService {
  private readonly config: FileValidationConfig;

  constructor() {
    this.config = environment.upload;
  }

  /**
   * Validate a file for upload.
   * 
   * @param file - File to validate
   * @returns ValidationResult with valid flag and optional error message
   */
  validateFile(file: File): ValidationResult {
    // Validate extension
    const extensionResult = this.validateExtension(file.name);
    if (!extensionResult.valid) {
      return extensionResult;
    }

    // Validate size
    return this.validateSize(file.name, file.size);
  }

  /**
   * Validate file extension.
   * 
   * @param filename - Name of the file
   * @returns ValidationResult
   */
  validateExtension(filename: string): ValidationResult {
    const extension = this.getExtension(filename);
    
    if (!this.config.allowedExtensions.includes(extension)) {
      return {
        valid: false,
        error: `Invalid file type. Allowed: ${this.config.allowedExtensions.join(', ')}`
      };
    }

    return { valid: true };
  }

  /**
   * Validate file size based on type.
   * 
   * @param filename - Name of the file
   * @param sizeBytes - Size in bytes
   * @returns ValidationResult
   */
  validateSize(filename: string, sizeBytes: number): ValidationResult {
    const extension = this.getExtension(filename);
    const maxSize = this.getMaxSizeForExtension(extension);

    if (sizeBytes > maxSize) {
      const maxSizeMB = maxSize / 1024 / 1024;
      return {
        valid: false,
        error: `File too large. Maximum size: ${maxSizeMB}MB`
      };
    }

    return { valid: true };
  }

  /**
   * Get the maximum allowed size for a file extension.
   * 
   * @param extension - File extension (e.g., '.pdf')
   * @returns Maximum size in bytes
   */
  getMaxSizeForExtension(extension: string): number {
    if (extension === '.pdf') {
      return this.config.maxPdfSizeBytes;
    }
    if (['.png', '.jpg', '.jpeg', '.tiff', '.bmp'].includes(extension)) {
      return this.config.maxImageSizeBytes;
    }
    return this.config.maxFileSizeBytes;
  }

  /**
   * Get file extension from filename.
   * 
   * @param filename - Name of the file
   * @returns Lowercase extension with dot (e.g., '.pdf')
   */
  getExtension(filename: string): string {
    return '.' + (filename.split('.').pop()?.toLowerCase() || '');
  }

  /**
   * Get allowed extensions.
   * 
   * @returns Array of allowed extensions
   */
  getAllowedExtensions(): string[] {
    return [...this.config.allowedExtensions];
  }

  /**
   * Format file size for display.
   * 
   * @param bytes - Size in bytes
   * @returns Human-readable size string
   */
  formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  }
}
