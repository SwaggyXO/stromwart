import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as stylex from '@stylexjs/stylex';
import { Info, RefreshCw, ExternalLink } from 'lucide-react';
import { glassProps, formControl, pageLayout } from '@/lib/stylex';
import { useDiscoverModels, useProviderGuide } from '@/api/providers';
import {
  useEvalSummary,
  useEvalTraces,
  useFailureClusters,
  useProviders,
  useSettings,
  useTestProvider,
  useUpdateSettings,
} from '@/api/settings';
import AsyncButton from '@/components/ui/AsyncButton';
import LoadingScreen from '@/components/ui/LoadingScreen';
import Select from '@/components/ui/Select';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';
import {
  buildSavePayload,
  isLlmDirty,
  settingsEqual,
  touchesLlmSettings,
} from '@/lib/settingsDraft';
import { toast } from '@/lib/toast';
import { formatAgentDurationMs } from '@/lib/agentDisplay';
import EvalTraceTable from '@/components/evals/EvalTraceTable';
import type {
  AutonomyLevel,
  LlmProvider,
  SystemSettings,
} from '@/types';

type Tab = 'models' | 'thresholds' | 'evals' | 'sources';

function parseSetupSteps(text: string): string[] {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.replace(/^\d+\.\s*/, ''));
}

const styles = stylex.create({
  title: {
    fontSize: 22,
    fontWeight: 700,
    color: 'var(--sw-text)',
    margin: 0,
  },
  subtitle: {
    fontSize: 13,
    color: 'var(--sw-text-muted)',
    margin: 0,
  },
  tabs: {
    display: 'flex',
    gap: 8,
    padding: 4,
    borderRadius: 'var(--sw-radius-lg)',
    backgroundColor: 'var(--sw-surface-2)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
    width: 'fit-content',
  },
  tab: {
    paddingTop: 8,
    paddingBottom: 8,
    paddingLeft: 16,
    paddingRight: 16,
    borderRadius: 'var(--sw-radius-md)',
    borderWidth: 0,
    borderStyle: 'none',
    backgroundColor: {
      default: 'transparent',
      ':hover': 'rgba(255,255,255,0.04)',
    },
    color: 'var(--sw-text-muted)',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    transitionProperty: 'color, background-color, box-shadow',
    transitionDuration: '180ms',
    transitionTimingFunction: 'cubic-bezier(0.16, 1, 0.3, 1)',
  },
  tabActive: {
    color: '#ffffff',
    backgroundColor: 'var(--sw-accent)',
    boxShadow: '0 2px 10px rgba(249,115,22,0.35)',
  },
  card: {
    padding: 22,
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  label: {
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--sw-text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.07em',
  },
  row: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 16,
  },
  switchRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 8,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'var(--sw-border)',
  },
  switchLabel: {
    fontSize: 13,
    color: 'var(--sw-text)',
  },
  actions: {
    display: 'flex',
    gap: 10,
    alignItems: 'center',
  },
  secondaryBtn: {
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 18,
    paddingRight: 18,
    borderRadius: 'var(--sw-radius-md)',
    backgroundColor: {
      default: 'transparent',
      ':hover': 'rgba(255,255,255,0.04)',
    },
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
    color: 'var(--sw-text-muted)',
    fontSize: 13,
    cursor: 'pointer',
    transitionProperty: 'background-color, border-color, color',
    transitionDuration: '180ms',
  },
  status: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
  },
  ok: { color: 'var(--sw-green)' },
  err: { color: 'var(--sw-red)' },
  rangeValue: {
    fontSize: 12,
    fontFamily: 'var(--font-mono)',
    color: 'var(--sw-accent)',
  },
  metricGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
    gap: 12,
  },
  metricCard: {
    padding: 14,
  },
  metricName: {
    fontSize: 12,
    fontWeight: 700,
    color: 'var(--sw-accent)',
    textTransform: 'capitalize',
    marginBottom: 6,
  },
  metricBody: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
  },
  pre: {
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
    color: 'var(--sw-text-muted)',
    whiteSpace: 'pre-wrap',
    maxHeight: 240,
    overflow: 'auto',
  },
  metricRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    paddingTop: 4,
    paddingBottom: 4,
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'rgba(255,255,255,0.04)',
  },
  traceTable: {
    overflowX: 'auto',
    fontSize: 12,
  },
  traceTableInner: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  traceTh: {
    textAlign: 'left',
    padding: '8px 10px',
    fontSize: 10,
    fontWeight: 700,
    color: 'var(--sw-text-faint)',
    letterSpacing: '0.07em',
    textTransform: 'uppercase',
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'var(--sw-border)',
  },
  traceTd: {
    padding: '8px 10px',
    color: 'var(--sw-text-muted)',
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'rgba(255,255,255,0.04)',
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
  },
  clusterList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  clusterItem: {
    padding: 0,
    overflow: 'hidden',
  },
  clusterSummary: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    cursor: 'pointer',
    padding: 12,
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--sw-text)',
  },
  clusterBadge: {
    fontSize: 11,
    padding: '2px 8px',
    borderRadius: 'var(--sw-radius-sm)',
    backgroundColor: 'rgba(239,68,68,0.15)',
    color: '#ef4444',
    fontWeight: 600,
  },
  clusterBody: {
    padding: 12,
    paddingTop: 0,
    fontSize: 12,
    color: 'var(--sw-text-muted)',
  },
  sampleTrace: {
    padding: '4px 0',
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
  },
  emptyState: {
    textAlign: 'center',
    padding: 20,
    fontSize: 13,
    color: 'var(--sw-text-faint)',
  },
  sourceGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  sourceCard: {
    padding: 16,
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  sourceHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  sourceLabel: {
    fontSize: 14,
    fontWeight: 600,
    color: 'var(--sw-text)',
  },
  sourceTypeBadge: {
    fontSize: 10,
    padding: '2px 8px',
    borderRadius: 'var(--sw-radius-sm)',
    backgroundColor: 'var(--sw-accent-dim)',
    color: 'var(--sw-accent)',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  comingSoon: {
    fontSize: 10,
    padding: '2px 8px',
    borderRadius: 'var(--sw-radius-sm)',
    backgroundColor: 'rgba(255,255,255,0.06)',
    color: 'var(--sw-text-faint)',
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  activeBadge: {
    fontSize: 10,
    padding: '2px 8px',
    borderRadius: 'var(--sw-radius-sm)',
    backgroundColor: 'var(--sw-green-dim)',
    color: 'var(--sw-green)',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  sourcesHint: {
    fontSize: 13,
    color: 'var(--sw-text-muted)',
    marginBottom: 16,
    lineHeight: 1.5,
  },
  discoveryRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    marginTop: 4,
  },
  discoverBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '6px 12px',
    fontSize: 11,
    fontWeight: 600,
    borderRadius: 'var(--sw-radius-md)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
    backgroundColor: 'transparent',
    color: 'var(--sw-text-muted)',
    cursor: 'pointer',
  },
  discoveryOk: {
    fontSize: 11,
    color: 'var(--sw-green)',
    fontWeight: 600,
  },
  discoveryErr: {
    fontSize: 11,
    color: '#ef4444',
    fontWeight: 600,
  },
  guideCard: {
    marginTop: 8,
    padding: 0,
    overflow: 'hidden',
  },
  guideSummary: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    cursor: 'pointer',
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--sw-text)',
  },
  freeBadge: {
    fontSize: 9,
    padding: '2px 6px',
    borderRadius: 'var(--sw-radius-sm)',
    backgroundColor: 'rgba(34,197,94,0.15)',
    color: 'var(--sw-green)',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  guideBody: {
    padding: '0 12px 12px',
  },
  guideDesc: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    marginBottom: 8,
  },
  guideStepList: {
    margin: 0,
    paddingTop: 12,
    paddingBottom: 12,
    paddingLeft: 28,
    paddingRight: 12,
    fontSize: 11,
    fontFamily: 'var(--font-mono)',
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderRadius: 'var(--sw-radius-md)',
    color: 'var(--sw-text)',
    lineHeight: 1.6,
  },
  guideStepItem: {
    marginBottom: 6,
    color: 'var(--sw-text)',
  },
  guideLink: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    marginTop: 8,
    fontSize: 11,
    color: 'var(--sw-accent)',
    textDecoration: 'none',
  },
  saveBar: {
    position: 'sticky',
    bottom: 16,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
    paddingTop: 14,
    paddingBottom: 14,
    paddingLeft: 18,
    paddingRight: 18,
    borderRadius: 'var(--sw-radius-lg)',
    backgroundColor: 'var(--sw-surface-2)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
    boxShadow: '0 8px 32px rgba(0,0,0,0.35)',
    zIndex: 20,
  },
  saveBarLabel: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--sw-text-muted)',
  },
  saveBarActions: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
});

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>('models');
  const { data: settings, isLoading } = useSettings();
  const { data: providers = [] } = useProviders();
  const update = useUpdateSettings();
  const testProvider = useTestProvider();
  const { data: evalSummary } = useEvalSummary();
  const { data: traces } = useEvalTraces(20);
  const { data: clustersData } = useFailureClusters();
  const clusters = clustersData?.clusters ?? [];
  const traceList = traces?.traces ?? [];

  const [saved, setSaved] = useState<Partial<SystemSettings>>({});
  const [draft, setDraft] = useState<Partial<SystemSettings>>({});
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const hydratedRef = useRef(false);

  const discover = useDiscoverModels();
  const { data: guide } = useProviderGuide(draft.llm_provider ?? null);

  useEffect(() => {
    if (!settings || hydratedRef.current) return;
    setSaved(settings);
    setDraft(settings);
    setConnectionStatus(settings.llm_connection_verified ? 'success' : 'idle');
    hydratedRef.current = true;
  }, [settings]);

  const discoveredModels = draft.llm_discovered_models ?? [];

  const selectedProvider = useMemo(
    () => providers.find((p) => p.id === draft.llm_provider),
    [providers, draft.llm_provider],
  );

  const isDirty = !settingsEqual(draft, saved);
  const llmDirty = isLlmDirty(draft, saved);
  const canSave =
    isDirty &&
    (!llmDirty || draft.llm_provider === 'disabled' || connectionStatus === 'success');

  useUnsavedChanges(isDirty);

  const updateDraft = useCallback((changes: Partial<SystemSettings>) => {
    setDraft((current) => ({ ...current, ...changes }));
    if (touchesLlmSettings(changes)) {
      setConnectionStatus('idle');
    }
  }, []);

  const handleDiscard = () => {
    setDraft(saved);
    setConnectionStatus(saved.llm_connection_verified ? 'success' : 'idle');
  };

  const handleSave = async () => {
    if (!canSave) return;
    try {
      const payload = buildSavePayload(draft, saved, connectionStatus === 'success');
      const updated = await update.mutateAsync(payload);
      setSaved(updated);
      setDraft(updated);
      setConnectionStatus(updated.llm_connection_verified ? 'success' : 'idle');
      toast.success('Settings saved');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to save settings');
    }
  };

  const handleTestConnection = async () => {
    try {
      const result = await testProvider.mutateAsync({
        provider_id: String(draft.llm_provider),
        model: draft.llm_model ?? '',
        api_key: draft.llm_api_key ?? undefined,
        endpoint: draft.llm_endpoint ?? undefined,
      });
      if (result.success) {
        setConnectionStatus('success');
        const message =
          result.latency_ms > 0
            ? `${result.message} (${result.latency_ms}ms)`
            : result.message;
        toast.success(message);
      } else {
        setConnectionStatus('error');
        toast.error(result.message || 'Connection failed');
      }
    } catch (error) {
      setConnectionStatus('error');
      const message =
        error instanceof Error && error.message.includes('timed out')
          ? 'Connection timed out'
          : error instanceof Error
            ? error.message
            : 'Connection failed';
      toast.error(message);
    }
  };

  const handleDiscoverModels = async () => {
    try {
      const result = await discover.mutateAsync({
        provider_id: String(draft.llm_provider),
        api_key: draft.llm_api_key ?? undefined,
        endpoint: draft.llm_endpoint ?? undefined,
      });
      if (result.status === 'connected' && result.models.length > 0) {
        updateDraft({
          llm_discovered_models: result.models,
          llm_model: result.models.includes(draft.llm_model ?? '')
            ? draft.llm_model
            : result.models[0],
        });
        toast.success(`${result.models.length} models found`);
      } else if (result.status === 'connected') {
        updateDraft({ llm_discovered_models: [] });
        toast.success(result.message ?? 'Connected — no models listed');
      } else {
        toast.error(result.message ?? 'Discovery failed');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Discovery failed');
    }
  };

  if (isLoading && !settings) return <LoadingScreen message="Loading settings…" />;

  return (
    <div {...stylex.props(pageLayout.containerNarrow)}>
      <div>
        <h1 {...stylex.props(styles.title)}>Settings</h1>
        <p {...stylex.props(styles.subtitle)}>
          LLM providers, alert thresholds, agent eval configuration, and data sources.
        </p>
      </div>

      <div {...stylex.props(styles.tabs)}>
        {(
          [
            ['models', 'Models'],
            ['thresholds', 'Thresholds'],
            ['evals', 'Evals'],
            ['sources', 'Data Sources'],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            {...stylex.props(styles.tab, tab === id && styles.tabActive)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'models' && (
        <div {...glassProps(styles.card)}>
          <div {...stylex.props(styles.row)}>
            <div {...stylex.props(styles.field)}>
              <label {...stylex.props(styles.label)}>Provider</label>
              <Select
                aria-label="Provider"
                value={draft.llm_provider ?? 'disabled'}
                options={
                  providers.length === 0
                    ? [{ value: 'disabled', label: 'disabled' }]
                    : providers.map((p) => ({
                        value: p.id,
                        label: `${p.name}${p.free_tier ? ' (free)' : ''}`,
                      }))
                }
                onChange={(provider_id) => {
                  const provider = providers.find((p) => p.id === provider_id);
                  updateDraft({
                    llm_provider: provider_id as LlmProvider,
                    llm_model: provider?.models[0] ?? '',
                    llm_discovered_models: [],
                  });
                }}
              />
            </div>
            <div {...stylex.props(styles.field)}>
              <label {...stylex.props(styles.label)}>Model</label>
              <Select
                aria-label="Model"
                value={draft.llm_model ?? ''}
                options={(
                  discoveredModels.length > 0
                    ? discoveredModels
                    : (selectedProvider?.models ?? [draft.llm_model ?? ''])
                ).map((m) => ({
                  value: m,
                  label: m || '(none)',
                }))}
                onChange={(llm_model) => updateDraft({ llm_model })}
              />
              <div {...stylex.props(styles.discoveryRow)}>
                <AsyncButton
                  variant="compact"
                  icon={RefreshCw}
                  loading={discover.isPending}
                  loadingLabel="Discovering…"
                  disabled={draft.llm_provider === 'disabled'}
                  onClick={handleDiscoverModels}
                >
                  Discover Models
                </AsyncButton>
                {discoveredModels.length > 0 && (
                  <span {...stylex.props(styles.discoveryOk)}>
                    {discoveredModels.length} models available
                  </span>
                )}
              </div>
            </div>
          </div>

          {guide && draft.llm_provider !== 'disabled' && (
            <details {...glassProps(styles.guideCard)}>
              <summary {...stylex.props(styles.guideSummary)}>
                <Info size={14} />
                <span>Setup Guide: {guide.title}</span>
                {guide.free === 'true' && (
                  <span {...stylex.props(styles.freeBadge)}>FREE</span>
                )}
              </summary>
              <div {...stylex.props(styles.guideBody)}>
                <p {...stylex.props(styles.guideDesc)}>{guide.description}</p>
                <ol {...stylex.props(styles.guideStepList)}>
                  {parseSetupSteps(guide.setup_steps).map((step, i) => (
                    <li key={i} {...stylex.props(styles.guideStepItem)}>
                      {step}
                    </li>
                  ))}
                </ol>
                <a
                  href={guide.docs_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  {...stylex.props(styles.guideLink)}
                >
                  <ExternalLink size={12} /> Open documentation
                </a>
              </div>
            </details>
          )}

          {(selectedProvider?.requires_api_key || draft.llm_provider === 'openai') && (
            <div {...stylex.props(styles.field)}>
              <label {...stylex.props(styles.label)}>API Key</label>
              <input
                type="password"
                {...stylex.props(formControl.field, formControl.input)}
                value={draft.llm_api_key ?? ''}
                onChange={(e) => updateDraft({ llm_api_key: e.target.value || null })}
                placeholder="••••••••"
              />
            </div>
          )}

          {(selectedProvider?.requires_endpoint || draft.llm_provider === 'ollama') && (
            <div {...stylex.props(styles.field)}>
              <label {...stylex.props(styles.label)}>Endpoint</label>
              <input
                {...stylex.props(formControl.field, formControl.input)}
                value={draft.llm_endpoint ?? ''}
                onChange={(e) => updateDraft({ llm_endpoint: e.target.value || null })}
                placeholder="http://localhost:11434"
              />
            </div>
          )}

          <div {...stylex.props(styles.actions)}>
            <AsyncButton
              loading={testProvider.isPending}
              loadingLabel="Testing…"
              disabled={!draft.llm_provider || draft.llm_provider === 'disabled'}
              onClick={handleTestConnection}
            >
              Test Connection
            </AsyncButton>
          </div>
        </div>
      )}

      {tab === 'thresholds' && (
        <div {...glassProps(styles.card)}>
          {(
            [
              ['alert_mos_threshold', 'Alert MOS threshold', 1, 5, 0.1],
              ['alert_buffer_ratio_threshold', 'Buffer ratio threshold', 0, 100, 0.5],
              ['alert_stall_count_threshold', 'Stall count threshold', 0, 50, 1],
              ['policy_min_confidence', 'Policy min confidence', 0, 1, 0.05],
              ['policy_max_blast_radius', 'Max blast radius', 0, 200000, 1000],
              ['policy_high_risk_threshold', 'High risk threshold', 0, 1, 0.05],
            ] as const
          ).map(([key, label, min, max, step]) => (
            <div key={key} {...stylex.props(styles.field)}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <label {...stylex.props(styles.label)}>{label}</label>
                <span {...stylex.props(styles.rangeValue)}>
                  {String(draft[key] ?? '')}
                </span>
              </div>
              <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={Number(draft[key] ?? min)}
                onChange={(e) => {
                  const v = Number(e.target.value);
                  updateDraft({ [key]: v });
                }}
              />
            </div>
          ))}

          <div {...stylex.props(styles.field)}>
            <label {...stylex.props(styles.label)}>Autonomy level</label>
            <Select
              aria-label="Autonomy level"
              value={draft.autonomy_level ?? 'recommend'}
              options={(
                ['observe_only', 'recommend', 'auto_simulate', 'auto_execute'] as const
              ).map((a) => ({ value: a, label: a }))}
              onChange={(v) => updateDraft({ autonomy_level: v as AutonomyLevel })}
            />
          </div>
        </div>
      )}

      {tab === 'evals' && (
        <div {...glassProps(styles.card)}>
          {(
            [
              ['detector_enabled', 'Detector'],
              ['diagnostician_enabled', 'Diagnostician'],
              ['mitigator_enabled', 'Mitigator'],
              ['verifier_enabled', 'Verifier'],
              ['eval_enabled', 'Eval enabled'],
              ['eval_llm_judge_enabled', 'LLM judge'],
            ] as const
          ).map(([key, label]) => (
            <div key={key} {...stylex.props(styles.switchRow)}>
              <span {...stylex.props(styles.switchLabel)}>{label}</span>
              <input
                type="checkbox"
                checked={Boolean(draft[key])}
                onChange={(e) => updateDraft({ [key]: e.target.checked })}
              />
            </div>
          ))}

          <div {...stylex.props(styles.field)}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label {...stylex.props(styles.label)}>Trace sample rate</label>
              <span {...stylex.props(styles.rangeValue)}>
                {draft.eval_trace_sample_rate ?? 1}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={Number(draft.eval_trace_sample_rate ?? 1)}
              onChange={(e) =>
                updateDraft({ eval_trace_sample_rate: Number(e.target.value) })
              }
            />
          </div>

          <div {...stylex.props(styles.label)}>Eval summary</div>
          {evalSummary?.agents?.length ? (
            <div {...stylex.props(styles.metricGrid)}>
              {evalSummary.agents.map((agent) => (
                <div key={agent.name} {...glassProps(styles.metricCard)}>
                  <div {...stylex.props(styles.metricName)}>{agent.name}</div>
                  <div {...stylex.props(styles.metricRow)}>
                    <span>Success rate</span>
                    <strong>{((1 - agent.failure_rate) * 100).toFixed(1)}%</strong>
                  </div>
                  <div {...stylex.props(styles.metricRow)}>
                    <span>Avg latency</span>
                    <strong>{formatAgentDurationMs(agent.avg_latency_ms)}</strong>
                  </div>
                  <div {...stylex.props(styles.metricRow)}>
                    <span>Total runs</span>
                    <strong>{agent.total_runs}</strong>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div {...stylex.props(styles.emptyState)}>
              No agent metrics yet. Run a simulation to generate eval data.
            </div>
          )}

          <div {...stylex.props(styles.label)}>Recent traces</div>
          {traceList.length > 0 ? (
            <EvalTraceTable traces={traceList} clusters={clusters} />
          ) : (
            <div {...stylex.props(styles.emptyState)}>No traces recorded yet.</div>
          )}

          <div {...stylex.props(styles.label)}>Failure clusters</div>
          {clusters.length > 0 ? (
            <div {...stylex.props(styles.clusterList)}>
              {clusters.map((cluster) => (
                <details key={cluster.cluster_id} {...glassProps(styles.clusterItem)}>
                  <summary {...stylex.props(styles.clusterSummary)}>
                    <span>{cluster.label || cluster.cluster_id}</span>
                    <span {...stylex.props(styles.clusterBadge)}>
                      {cluster.count} failures
                    </span>
                  </summary>
                  <div {...stylex.props(styles.clusterBody)}>
                    {cluster.representative_trace_id && (
                      <p>Representative trace: {cluster.representative_trace_id}</p>
                    )}
                    {Object.entries(cluster.common_attributes ?? {}).map(([key, value]) => (
                      <div key={key} {...stylex.props(styles.sampleTrace)}>
                        {key}: {String(value)}
                      </div>
                    ))}
                  </div>
                </details>
              ))}
            </div>
          ) : (
            <div {...stylex.props(styles.emptyState)}>No failure clusters detected.</div>
          )}
        </div>
      )}

      {tab === 'sources' && (
        <div {...glassProps(styles.card)}>
          <p {...stylex.props(styles.sourcesHint)}>
            Demo Scenario is the only available data source during Phase 1. Prometheus and
            WebSocket integrations are not ready yet.
          </p>
          <div {...stylex.props(styles.sourceGrid)}>
            {(draft.data_sources ?? []).map((source, index) => (
              <div key={`${source.type}-${index}`} {...glassProps(styles.sourceCard)}>
                <div {...stylex.props(styles.sourceHeader)}>
                  <div>
                    <div {...stylex.props(styles.sourceLabel)}>{source.label}</div>
                    <span {...stylex.props(styles.sourceTypeBadge)}>{source.type}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {source.type === 'simulation' ? (
                      <span {...stylex.props(styles.activeBadge)}>Active</span>
                    ) : (
                      <span {...stylex.props(styles.comingSoon)}>Coming soon</span>
                    )}
                  </div>
                </div>
                {(source.type === 'prometheus' || source.type === 'websocket') && (
                  <input
                    {...stylex.props(formControl.field, formControl.input)}
                    value={source.endpoint ?? ''}
                    placeholder={
                      source.type === 'prometheus'
                        ? 'http://prometheus:9090'
                        : 'wss://telemetry.example.com/stream'
                    }
                    disabled
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {isDirty && (
        <div {...glassProps(styles.saveBar)}>
          <span {...stylex.props(styles.saveBarLabel)}>Unsaved changes</span>
          <div {...stylex.props(styles.saveBarActions)}>
            <AsyncButton variant="secondary" onClick={handleDiscard}>
              Discard
            </AsyncButton>
            <AsyncButton
              loading={update.isPending}
              loadingLabel="Saving…"
              disabled={!canSave}
              onClick={handleSave}
            >
              Save changes
            </AsyncButton>
          </div>
        </div>
      )}
    </div>
  );
}
