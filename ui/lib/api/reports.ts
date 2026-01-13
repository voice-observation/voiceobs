/**
 * Reports API client (mock data implementation).
 */

import { BaseApiClient, simulateDelay } from "./base";
import type {
  Report,
  ReportGenerateRequest,
  ReportGenerateResponse,
  ScheduledReport,
  ScheduledReportCreateRequest,
  ScheduledReportsListResponse,
  ReportHistoryResponse,
  ReportHistoryFilters,
} from "../types";
import { mockReports, mockScheduledReports, mockReportHistory } from "../mockData";

// In-memory storage for reports
const inMemoryStore = {
  reports: [...mockReports],
  scheduledReports: [...mockScheduledReports],
  reportHistory: [...mockReportHistory],
};

export class ReportsApi extends BaseApiClient {
  /**
   * Generate a new report.
   */
  async generateReport(config: ReportGenerateRequest): Promise<ReportGenerateResponse> {
    await simulateDelay(600);
    const newReport: Report = {
      id: `report-${Date.now()}`,
      name: config.name,
      type: config.type,
      format: config.format || "json",
      status: "generating",
      config: config.config || {},
      generated_at: null,
      download_url: null,
      created_at: new Date().toISOString(),
    };
    inMemoryStore.reports.push(newReport);
    // Simulate report generation completion
    setTimeout(() => {
      const report = inMemoryStore.reports.find((r) => r.id === newReport.id);
      if (report) {
        report.status = "completed";
        report.generated_at = new Date().toISOString();
        report.download_url = `/api/reports/${report.id}/download`;
      }
      // Add to history
      inMemoryStore.reportHistory.unshift({
        id: `history-${Date.now()}`,
        report_id: newReport.id,
        name: newReport.name,
        status: "completed",
        generated_at: new Date().toISOString(),
        download_url: `/api/reports/${newReport.id}/download`,
      });
    }, 3000);
    return {
      report_id: newReport.id,
      status: "generating",
      estimated_completion_time: new Date(Date.now() + 3000).toISOString(),
    };
  }

  /**
   * List all scheduled reports.
   */
  async listScheduledReports(): Promise<ScheduledReportsListResponse> {
    await simulateDelay();
    return {
      count: inMemoryStore.scheduledReports.length,
      schedules: inMemoryStore.scheduledReports,
    };
  }

  /**
   * Create a new scheduled report.
   */
  async createSchedule(data: ScheduledReportCreateRequest): Promise<ScheduledReport> {
    await simulateDelay(500);
    const newSchedule: ScheduledReport = {
      id: `schedule-${Date.now()}`,
      name: data.name,
      report_type: data.report_type,
      format: data.format || "json",
      schedule: data.schedule,
      config: data.config || {},
      is_active: data.is_active !== undefined ? data.is_active : true,
      last_run: null,
      next_run: null, // Would calculate from cron expression in real implementation
      created_at: new Date().toISOString(),
    };
    inMemoryStore.scheduledReports.push(newSchedule);
    return newSchedule;
  }

  /**
   * Get report history with optional filtering.
   */
  async getReportHistory(filters?: ReportHistoryFilters): Promise<ReportHistoryResponse> {
    await simulateDelay();
    let reports = inMemoryStore.reportHistory;
    if (filters?.status) {
      reports = reports.filter((r) => r.status === filters.status);
    }
    if (filters?.type) {
      // Filter by type through report lookup
      reports = reports.filter((r) => {
        const report = inMemoryStore.reports.find((rep) => rep.id === r.report_id);
        return report?.type === filters.type;
      });
    }
    if (filters?.date_from) {
      const fromDate = new Date(filters.date_from);
      reports = reports.filter((r) => {
        if (!r.generated_at) return false;
        return new Date(r.generated_at) >= fromDate;
      });
    }
    if (filters?.date_to) {
      const toDate = new Date(filters.date_to);
      reports = reports.filter((r) => {
        if (!r.generated_at) return false;
        return new Date(r.generated_at) <= toDate;
      });
    }
    return {
      count: reports.length,
      reports,
    };
  }

  /**
   * Download a report.
   */
  async downloadReport(id: string): Promise<Blob> {
    await simulateDelay(800);
    const report = inMemoryStore.reports.find((r) => r.id === id);
    if (!report) {
      throw new Error(`Report '${id}' not found`);
    }
    if (report.status !== "completed" || !report.download_url) {
      throw new Error(`Report '${id}' is not ready for download`);
    }
    // Simulate file download - return a mock blob
    const mockContent = JSON.stringify({
      report_id: report.id,
      name: report.name,
      type: report.type,
      generated_at: report.generated_at,
      data: "Mock report data...",
    });
    return new Blob([mockContent], { type: "application/json" });
  }
}
