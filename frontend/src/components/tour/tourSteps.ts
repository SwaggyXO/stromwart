export interface TourStep {
  target: string;
  title: string;
  content: string;
  /** Floating-ui placement relative to the highlighted target. */
  placement?: 'top' | 'bottom' | 'left' | 'right';
}

export const onboardingSteps: TourStep[] = [
  {
    target: '[data-tour="kpi-panel"]',
    title: 'Real-Time KPIs',
    content:
      'These cards show live quality metrics — active sessions and incident pressure from the SSE stream. They update as the pipeline pushes LiveEventUpdate payloads.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="forecast-chart"]',
    title: 'QoE Forecast',
    content:
      'The forecast chart shows event-scoped degradation risk (p10–p90) from the QoE forecaster.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="alert-feed"]',
    title: 'Alert Feed',
    content:
      'Alerts surface evidence tied to incidents. Acknowledge actions require a backend alerts API when available.',
    placement: 'top',
  },
  {
    target: '[data-tour="incident-card"]',
    title: 'Incidents & Root Cause',
    content:
      'Incidents arrive on the live stream. Open one to review root-cause analysis, evidence, and remediation proposals.',
    placement: 'top',
  },
  {
    target: '[data-tour="proposal-actions"]',
    title: 'Propose, Simulate, Approve',
    content:
      'Each remediation proposal passes through a deterministic policy gate. Run a simulation, then approve or reject based on the outcome.',
    placement: 'top',
  },
  {
    target: '[data-tour="audit-link"]',
    title: 'Full Audit Trail',
    content:
      'Every decision — human or AI — is logged with a correlation ID. Navigate here to see the complete provenance chain for compliance.',
    placement: 'right',
  },
];
