import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import ProgressBar from '../ProgressBar.svelte';

describe('ProgressBar', () => {
  it('renders score as percentage text', () => {
    render(ProgressBar, { props: { score: 75 } });
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('renders label when provided', () => {
    render(ProgressBar, { props: { score: 50, label: 'Jul 18' } });
    expect(screen.getByText('Jul 18')).toBeInTheDocument();
  });

  it('has correct progressbar role and aria values', () => {
    render(ProgressBar, { props: { score: 80 } });
    const bar = screen.getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-valuenow', '80');
    expect(bar).toHaveAttribute('aria-valuemax', '100');
  });

  it('renders 0% correctly', () => {
    render(ProgressBar, { props: { score: 0 } });
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('renders 100% correctly', () => {
    render(ProgressBar, { props: { score: 100 } });
    expect(screen.getByText('100%')).toBeInTheDocument();
  });
});
