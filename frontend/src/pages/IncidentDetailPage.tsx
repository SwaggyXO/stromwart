import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import * as stylex from '@stylexjs/stylex';
import { glassProps, pageLayout, primaryButtonProps } from '@/lib/stylex';
import { ArrowLeft, Brain, Shield, Play, CheckCircle, XCircle } from 'lucide-react';
import { format } from 'date-fns';
import { useIncidentDetail, useIncidentProposals } from '@/api/queries';
import {
  useApproveProposal,
  useRejectProposal,
  useResolveIncident,
  useSimulateAction,
} from '@/api/mutations';
import { useAppStore } from '@/store/useAppStore';
import SeverityBadge from '@/components/ui/SeverityBadge';
import PolicyBadge from '@/components/ui/PolicyBadge';
import LoadingScreen from '@/components/ui/LoadingScreen';
import { hypothesisText, sliceLabel, type ProposalState } from '@/types';
import { hypothesisSourceLabel } from '@/lib/agentDisplay';
import { toast } from '@/lib/toast';
import { ApiError } from '@/api/client';

const styles = stylex.create({
  back: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'transparent',
    borderWidth: 0,
    color: 'var(--sw-text-muted)',
    fontSize: 13,
    cursor: 'pointer',
    padding: 0,
    width: 'fit-content',
  },
  card: {
    padding: 24,
    position: 'relative',
    overflow: 'hidden',
  },
  gloss: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '40%',
    backgroundImage: 'linear-gradient(180deg, rgba(255,255,255,0.05) 0%, transparent 100%)',
    pointerEvents: 'none',
  },
  relative: { position: 'relative', zIndex: 1 },
  rowBetween: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 14,
  },
  mono: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    fontFamily: 'var(--font-mono)',
    marginBottom: 6,
  },
  badges: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  statePill: {
    paddingTop: 2,
    paddingBottom: 2,
    paddingLeft: 8,
    paddingRight: 8,
    borderRadius: 99,
    fontSize: 11,
    fontWeight: 600,
    backgroundColor: 'var(--sw-blue-dim)',
    color: 'var(--sw-blue)',
  },
  faint: {
    fontSize: 12,
    color: 'var(--sw-text-faint)',
  },
  label: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    marginBottom: 4,
  },
  value: {
    fontSize: 14,
    color: 'var(--sw-text)',
    fontFamily: 'var(--font-mono)',
  },
  sectionTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 14,
  },
  sectionTitleText: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--sw-text)',
  },
  aiPill: {
    paddingTop: 2,
    paddingBottom: 2,
    paddingLeft: 8,
    paddingRight: 8,
    borderRadius: 99,
    fontSize: 10,
    fontWeight: 700,
    backgroundColor: 'var(--sw-blue-dim)',
    color: 'var(--sw-blue)',
  },
  body: {
    fontSize: 14,
    color: 'var(--sw-text-muted)',
    lineHeight: 1.7,
    margin: 0,
  },
  evidenceRow: {
    marginTop: 14,
    display: 'flex',
    gap: 8,
    flexWrap: 'wrap',
  },
  evidenceChip: {
    paddingTop: 3,
    paddingBottom: 3,
    paddingLeft: 9,
    paddingRight: 9,
    borderRadius: 99,
    fontSize: 11,
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
    color: 'var(--sw-text-muted)',
    fontFamily: 'var(--font-mono)',
  },
  grid2: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 16,
    marginBottom: 16,
  },
  fieldLabel: {
    fontSize: 11,
    color: 'var(--sw-text-faint)',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: '0.07em',
  },
  fieldValue: {
    fontSize: 13,
    color: 'var(--sw-text)',
    fontFamily: 'var(--font-mono)',
  },
  fieldMuted: {
    fontSize: 13,
    color: 'var(--sw-text-muted)',
    lineHeight: 1.6,
    marginBottom: 10,
  },
  actions: {
    display: 'flex',
    gap: 10,
    flexWrap: 'wrap',
  },
  primaryBtn: {
    paddingLeft: 20,
    paddingRight: 20,
    display: 'flex',
    alignItems: 'center',
    gap: 7,
  },
  secondaryBtn: {
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 20,
    paddingRight: 20,
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
    display: 'flex',
    alignItems: 'center',
    gap: 7,
    transitionProperty: 'background-color, border-color, color',
    transitionDuration: '180ms',
  },
  blocked: {
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 14,
    paddingRight: 14,
    borderRadius: 'var(--sw-radius-md)',
    backgroundColor: 'var(--sw-blue-dim)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'rgba(59,130,246,0.25)',
    fontSize: 12,
    color: 'var(--sw-blue)',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  simResult: {
    marginTop: 12,
    padding: 12,
    borderRadius: 'var(--sw-radius-md)',
    backgroundColor: 'var(--sw-surface-2)',
    fontSize: 13,
    color: 'var(--sw-text-muted)',
    lineHeight: 1.5,
  },
  note: {
    fontSize: 12,
    color: 'var(--sw-text-faint)',
    lineHeight: 1.5,
  },
  actionHint: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    marginTop: 10,
    lineHeight: 1.5,
  },
  resolvedBanner: {
    marginTop: 12,
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 14,
    paddingRight: 14,
    borderRadius: 'var(--sw-radius-md)',
    backgroundColor: 'var(--sw-green-dim)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'rgba(34, 197, 94, 0.35)',
    fontSize: 12,
    color: 'var(--sw-green)',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  proposalIdInput: {
    width: '100%',
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 12,
    paddingRight: 12,
    borderRadius: 'var(--sw-radius-md)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
    backgroundColor: 'var(--sw-surface-2)',
    color: 'var(--sw-text)',
    fontFamily: 'var(--font-mono)',
    fontSize: 13,
    marginBottom: 12,
  },
});

export default function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth0();
  const { data: incident, isLoading } = useIncidentDetail(id);
  const { data: proposals = [] } = useIncidentProposals(id);
  const simulate = useSimulateAction();
  const approve = useApproveProposal();
  const reject = useRejectProposal();
  const resolve = useResolveIncident();
  const addAuditEvent = useAppStore((s) => s.addAuditEvent);
  const startSimulation = useAppStore((s) => s.startSimulation);
  const stopSimulation = useAppStore((s) => s.stopSimulation);

  const [simExplanation, setSimExplanation] = useState<string | null>(null);

  const proposal = proposals[0] ?? null;
  const proposalId = proposal?.id ?? '';

  const actorId = user?.sub ?? user?.email ?? 'operator';

  const proposalState = proposal?.state as ProposalState | undefined;
  const isResolved = incident?.state === 'resolved';

  const proposalActionHint =
    proposalState === 'approval_required'
      ? 'Approve to allow simulation.'
      : proposalState === 'simulate'
        ? 'Run simulation, then approve to sign off.'
        : proposalState === 'approved'
          ? 'Operator approved — resolve when remediation is complete.'
          : proposalState === 'blocked'
            ? 'This proposal was blocked or rejected.'
            : null;

  const showSimulate = !isResolved && proposalState === 'simulate';
  const showApproveReject =
    !isResolved &&
    (proposalState === 'approval_required' || proposalState === 'simulate');
  const showResolveOnly =
    !isResolved && (proposalState === 'approved' || proposalState === 'blocked');
  const approveLabel =
    proposalState === 'approval_required' ? 'Approve for Simulation' : 'Approve';

  const formatApiError = (error: unknown) => {
    if (error instanceof ApiError) {
      try {
        const parsed = JSON.parse(error.message) as { detail?: string };
        return parsed.detail ?? error.message;
      } catch {
        return error.message;
      }
    }
    return error instanceof Error ? error.message : 'Request failed';
  };

  if (isLoading) return <LoadingScreen message="Loading incident…" />;
  if (!incident) {
    return (
      <div {...stylex.props(pageLayout.containerNarrow)}>
        <div {...stylex.props(styles.note)}>Incident not found.</div>
      </div>
    );
  }

  const handleSimulate = async () => {
    if (!proposalId) return;
    startSimulation();
    try {
      const result = await simulate.mutateAsync(proposalId);
      setSimExplanation(result.explanation);
      addAuditEvent({
        correlation_id: incident.id,
        actor_type: 'human',
        artifact_type: 'proposal',
        artifact_id: proposalId,
        description: `Operator ran simulation for proposal ${proposalId}`,
      });
    } catch (error) {
      toast.error(formatApiError(error));
    } finally {
      stopSimulation();
    }
  };

  const handleApprove = async () => {
    if (!proposalId) return;
    try {
      await approve.mutateAsync({
        proposalId,
        body: {
          approved: true,
          actor_id: actorId,
          reason: 'Operator approved remediation',
        },
      });
      addAuditEvent({
        correlation_id: incident.id,
        actor_type: 'human',
        artifact_type: 'proposal',
        artifact_id: proposalId,
        description: `Operator approved proposal ${proposalId}`,
      });
      toast.success('Proposal approved');
    } catch (error) {
      toast.error(formatApiError(error));
    }
  };

  const handleReject = async () => {
    if (!proposalId) return;
    try {
      await reject.mutateAsync({
        proposalId,
        body: {
          actor_id: actorId,
          reason: 'Operator rejected remediation',
        },
      });
      addAuditEvent({
        correlation_id: incident.id,
        actor_type: 'human',
        artifact_type: 'proposal',
        artifact_id: proposalId,
        description: `Operator rejected proposal ${proposalId}`,
      });
      toast.success('Proposal rejected');
    } catch (error) {
      toast.error(formatApiError(error));
    }
  };

  const handleResolve = async () => {
    try {
      await resolve.mutateAsync(incident.id);
      addAuditEvent({
        correlation_id: incident.id,
        actor_type: 'human',
        artifact_type: 'incident',
        artifact_id: incident.id,
        description: `Operator resolved incident ${incident.id}`,
      });
      toast.success('Incident resolved');
      navigate('/');
    } catch (error) {
      toast.error(formatApiError(error));
    }
  };

  return (
    <div {...stylex.props(pageLayout.containerNarrow)}>
      <button type="button" onClick={() => navigate('/')} {...stylex.props(styles.back)}>
        <ArrowLeft size={14} /> Back to Live Event
      </button>

      <div {...glassProps(styles.card)}>
        <div {...stylex.props(styles.gloss)} />
        <div {...stylex.props(styles.relative)}>
          <div {...stylex.props(styles.rowBetween)}>
            <div>
              <div {...stylex.props(styles.mono)}>{incident.id}</div>
              <div {...stylex.props(styles.badges)}>
                <SeverityBadge severity={incident.severity} />
                <span {...stylex.props(styles.statePill)}>{incident.state}</span>
              </div>
            </div>
            <div {...stylex.props(styles.faint)}>
              {format(new Date(incident.created_at), 'MMM d, HH:mm:ss')}
            </div>
          </div>
          <div {...stylex.props(styles.label)}>Affected slice</div>
          <div {...stylex.props(styles.value)}>
            {incident.slice_key || sliceLabel(incident.affected_slice)}
          </div>
        </div>
      </div>

      <div {...glassProps(styles.card)}>
        <div {...stylex.props(styles.sectionTitle)}>
          <Brain size={16} color="var(--sw-blue)" />
          <span {...stylex.props(styles.sectionTitleText)}>
            {hypothesisSourceLabel(incident.hypothesis)}
          </span>
          <span {...stylex.props(styles.aiPill)}>
            {incident.hypothesis?.source === 'llm_analyst'
              ? 'LLM · evidence-grounded'
              : incident.hypothesis?.source === 'diagnostician'
                ? 'Deterministic RCA'
                : 'Awaiting analysis'}
          </span>
        </div>
        <p {...stylex.props(styles.body)}>{hypothesisText(incident.hypothesis)}</p>
        <div {...stylex.props(styles.evidenceRow)}>
          {incident.evidence_ids.map((eid) => (
            <span key={eid} {...stylex.props(styles.evidenceChip)}>
              {eid}
            </span>
          ))}
        </div>
      </div>

      <div {...glassProps(styles.card)}>
        <div {...stylex.props(styles.sectionTitle)}>
          <Shield size={16} color="var(--sw-accent)" />
          <span {...stylex.props(styles.sectionTitleText)}>Action Proposal</span>
          {proposal && <PolicyBadge state={proposal.state} />}
        </div>

        {proposal ? (
          <>
            <div {...stylex.props(styles.grid2)}>
              {[
                { label: 'Action type', value: proposal.action_type },
                {
                  label: 'Target scope',
                  value: JSON.stringify(proposal.target_scope),
                },
                {
                  label: 'Confidence',
                  value: `${(proposal.confidence * 100).toFixed(0)}%`,
                },
                {
                  label: 'Risk score',
                  value: `${(proposal.risk_score * 100).toFixed(0)}%`,
                },
              ].map(({ label, value }) => (
                <div key={label}>
                  <div {...stylex.props(styles.fieldLabel)}>{label}</div>
                  <div {...stylex.props(styles.fieldValue)}>{value}</div>
                </div>
              ))}
            </div>
            <div {...stylex.props(styles.fieldLabel)}>Rationale</div>
            <div {...stylex.props(styles.fieldMuted)}>{proposal.rationale}</div>
            <div {...stylex.props(styles.fieldLabel)}>Expected effect</div>
            <div {...stylex.props(styles.fieldMuted)}>{proposal.expected_effect}</div>
          </>
        ) : (
          <p {...stylex.props(styles.note)}>No proposals yet for this incident.</p>
        )}

        {(showSimulate || showApproveReject || showResolveOnly) && (
          <div data-tour="proposal-actions" {...stylex.props(styles.actions)}>
            {showSimulate && (
              <button
                type="button"
                onClick={handleSimulate}
                disabled={!proposalId || simulate.isPending}
                {...primaryButtonProps('default', styles.primaryBtn)}
              >
                <Play size={13} /> Run Simulation
              </button>
            )}
            {showApproveReject && (
              <>
                <button
                  type="button"
                  onClick={handleApprove}
                  disabled={!proposalId || approve.isPending}
                  {...stylex.props(styles.secondaryBtn)}
                >
                  <CheckCircle size={13} /> {approveLabel}
                </button>
                <button
                  type="button"
                  onClick={handleReject}
                  disabled={!proposalId || reject.isPending}
                  {...stylex.props(styles.secondaryBtn)}
                >
                  <XCircle size={13} /> Reject
                </button>
              </>
            )}
            {showResolveOnly && (
              <button
                type="button"
                onClick={handleResolve}
                disabled={resolve.isPending}
                {...primaryButtonProps('default', styles.primaryBtn)}
              >
                <CheckCircle size={13} /> Resolve Incident
              </button>
            )}
          </div>
        )}

        {isResolved && (
          <div {...stylex.props(styles.resolvedBanner)}>
            <CheckCircle size={13} />
            Incident resolved
            {incident.updated_at
              ? ` · ${format(new Date(incident.updated_at), 'MMM d, HH:mm')}`
              : ''}
          </div>
        )}

        {proposalActionHint && !isResolved && (
          <p {...stylex.props(styles.actionHint)}>{proposalActionHint}</p>
        )}

        {proposal?.state === 'blocked' && (
          <div {...stylex.props(styles.blocked)}>
            <XCircle size={13} />
            Policy verifier blocked action
            {proposal.policy_reasons?.length
              ? `: ${proposal.policy_reasons.join('; ')}`
              : '.'}
          </div>
        )}

        {simExplanation && (
          <div {...stylex.props(styles.simResult)}>
            Simulation: {simExplanation}
          </div>
        )}
      </div>
    </div>
  );
}
