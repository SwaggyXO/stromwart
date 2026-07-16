import * as stylex from '@stylexjs/stylex';
import { glassProps } from '@/lib/stylex';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { format } from 'date-fns';
import type { ForecastPoint } from '@/types';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const styles = stylex.create({
  card: {
    paddingTop: 20,
    paddingBottom: 12,
    paddingLeft: 20,
    paddingRight: 20,
  },
  header: {
    marginBottom: 16,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--sw-text)',
  },
  subtitle: {
    fontSize: 11,
    color: 'var(--sw-text-muted)',
  },
  badge: {
    paddingTop: 3,
    paddingBottom: 3,
    paddingLeft: 10,
    paddingRight: 10,
    borderRadius: 99,
    fontSize: 11,
    fontWeight: 600,
    backgroundColor: 'var(--sw-accent-dim)',
    color: 'var(--sw-accent)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'rgba(249,115,22,0.3)',
  },
  empty: {
    padding: 40,
    textAlign: 'center',
    fontSize: 13,
    color: 'var(--sw-text-faint)',
  },
});

export default function ForecastChart({ data }: { data: ForecastPoint[] }) {
  if (!data.length) {
    return (
      <div {...glassProps(styles.card)}>
        <div {...stylex.props(styles.header)}>
          <div>
            <div {...stylex.props(styles.title)}>Degradation Risk Forecast</div>
            <div {...stylex.props(styles.subtitle)}>P10 / P50 / P90 · event forecast series</div>
          </div>
        </div>
        <div {...stylex.props(styles.empty)}>No forecast data yet</div>
      </div>
    );
  }

  const labels = data.map((d) => format(new Date(d.timestamp), 'HH:mm'));
  const every = Math.max(1, Math.ceil(data.length / 12));

  return (
    <div {...glassProps(styles.card)}>
      <div {...stylex.props(styles.header)}>
        <div>
          <div {...stylex.props(styles.title)}>Degradation Risk Forecast</div>
          <div {...stylex.props(styles.subtitle)}>P10 / P50 / P90 · event forecast series</div>
        </div>
        <div {...stylex.props(styles.badge)}>Live</div>
      </div>
      <Line
        data={{
          labels,
          datasets: [
            {
              label: 'P90',
              data: data.map((d) => d.p90),
              borderColor: 'transparent',
              backgroundColor: 'rgba(249,115,22,0.12)',
              fill: '+1',
              tension: 0.4,
              pointRadius: 0,
            },
            {
              label: 'P50',
              data: data.map((d) => d.p50),
              borderColor: '#f97316',
              backgroundColor: 'transparent',
              borderWidth: 2,
              fill: false,
              tension: 0.4,
              pointRadius: 0,
            },
            {
              label: 'P10',
              data: data.map((d) => d.p10),
              borderColor: 'transparent',
              backgroundColor: 'rgba(249,115,22,0.06)',
              fill: '-1',
              tension: 0.4,
              pointRadius: 0,
            },
            {
              label: 'Actual',
              data: data.map((d) => d.actual ?? null),
              borderColor: 'rgba(255,255,255,0.5)',
              backgroundColor: 'transparent',
              borderWidth: 1.5,
              fill: false,
              tension: 0.3,
              pointRadius: 0,
              borderDash: [4, 4],
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: true,
          aspectRatio: 3,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: {
              display: true,
              labels: { color: '#8888aa', font: { size: 11 }, boxWidth: 12, padding: 16 },
            },
            tooltip: {
              backgroundColor: 'rgba(13,13,23,0.96)',
              borderColor: 'rgba(255,255,255,0.1)',
              borderWidth: 1,
              titleColor: '#e8e8f0',
              bodyColor: '#8888aa',
              padding: 10,
              callbacks: {
                label: (ctx) => {
                  const y = ctx.parsed.y;
                  if (y == null) return ` ${ctx.dataset.label}: —`;
                  return ` ${ctx.dataset.label}: ${(y * 100).toFixed(1)}%`;
                },
              },
            },
          },
          scales: {
            x: {
              grid: { color: 'rgba(255,255,255,0.04)' },
              ticks: {
                color: '#444466',
                font: { size: 10 },
                callback: (_v: unknown, i: number) => (i % every === 0 ? labels[i] : ''),
              },
            },
            y: {
              min: 0,
              max: 1,
              grid: { color: 'rgba(255,255,255,0.04)' },
              ticks: {
                color: '#444466',
                font: { size: 10 },
                callback: (v: unknown) => `${Math.round((v as number) * 100)}%`,
              },
            },
          },
        }}
      />
    </div>
  );
}
