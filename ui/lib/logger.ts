/**
 * Logger utility for handling logs across different environments.
 *
 * In development: Logs to console
 * In production: Can send to debugging services (Sentry, LogRocket, etc.)
 */

type LogLevel = "log" | "info" | "warn" | "error" | "debug";

interface LogContext {
  [key: string]: unknown;
}

class Logger {
  private isDevelopment: boolean;
  private isProduction: boolean;

  constructor() {
    // Check if we're in development mode
    this.isDevelopment =
      process.env.NODE_ENV === "development" ||
      process.env.NEXT_PUBLIC_ENV === "development" ||
      (typeof window !== "undefined" && window.location.hostname === "localhost");

    this.isProduction = !this.isDevelopment;
  }

  /**
   * Log a message with optional context.
   */
  log(message: string, context?: LogContext): void {
    this.handleLog("log", message, context);
  }

  /**
   * Log an info message.
   */
  info(message: string, context?: LogContext): void {
    this.handleLog("info", message, context);
  }

  /**
   * Log a warning message.
   */
  warn(message: string, context?: LogContext): void {
    this.handleLog("warn", message, context);
  }

  /**
   * Log an error message.
   */
  error(message: string, error?: Error | unknown, context?: LogContext): void {
    const errorContext: LogContext = {
      ...context,
      ...(error instanceof Error
        ? {
            error: {
              name: error.name,
              message: error.message,
              stack: error.stack,
            },
          }
        : { error }),
    };
    this.handleLog("error", message, errorContext);
  }

  /**
   * Log a debug message (only in development).
   */
  debug(message: string, context?: LogContext): void {
    if (this.isDevelopment) {
      this.handleLog("debug", message, context);
    }
  }

  /**
   * Internal method to handle logging based on environment.
   */
  private handleLog(level: LogLevel, message: string, context?: LogContext): void {
    if (this.isDevelopment) {
      // In development, log to console
      const consoleMethod = console[level] || console.log;
      if (context) {
        consoleMethod(`[${level.toUpperCase()}] ${message}`, context);
      } else {
        consoleMethod(`[${level.toUpperCase()}] ${message}`);
      }
    } else {
      // In production, send to debugging service
      this.sendToDebuggingService(level, message, context);
    }
  }

  /**
   * Send logs to a debugging service in production.
   * This can be extended to integrate with services like:
   * - Sentry
   * - LogRocket
   * - Datadog
   * - Custom logging endpoint
   */
  private sendToDebuggingService(
    level: LogLevel,
    message: string,
    context?: LogContext
  ): void {
    // Only send errors and warnings to debugging service in production
    // to avoid noise from debug/info logs
    if (level !== "error" && level !== "warn") {
      return;
    }

    try {
      // Example: Send to a custom logging endpoint
      // You can uncomment and configure this based on your needs
      /*
      if (typeof window !== "undefined" && window.fetch) {
        fetch("/api/logs", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            level,
            message,
            context,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent,
          }),
        }).catch(() => {
          // Silently fail if logging service is unavailable
        });
      }
      */

      // Example: Send to Sentry
      // if (typeof window !== "undefined" && (window as any).Sentry) {
      //   const Sentry = (window as any).Sentry;
      //   if (level === "error") {
      //     Sentry.captureException(new Error(message), {
      //       extra: context,
      //     });
      //   } else {
      //     Sentry.captureMessage(message, {
      //       level: level === "warn" ? "warning" : "info",
      //       extra: context,
      //     });
      //   }
      // }

      // Example: Send to LogRocket
      // if (typeof window !== "undefined" && (window as any).LogRocket) {
      //   const LogRocket = (window as any).LogRocket;
      //   LogRocket.log(level, message, context);
      // }

      // For now, we'll still log errors to console in production
      // but you can remove this once you've set up a debugging service
      if (level === "error") {
        console.error(`[PROD] ${message}`, context);
      } else if (level === "warn") {
        console.warn(`[PROD] ${message}`, context);
      }
    } catch (err) {
      // Silently fail if logging service integration fails
      // We don't want logging errors to break the app
    }
  }
}

// Export a singleton instance
export const logger = new Logger();

// Export the Logger class for custom instances if needed
export { Logger, type LogLevel, type LogContext };
