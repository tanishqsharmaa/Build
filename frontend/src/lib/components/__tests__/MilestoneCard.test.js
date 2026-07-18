import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import MilestoneCard from '../MilestoneCard.svelte';

describe('MilestoneCard', () => {
  it('renders topic text', () => {
    render(MilestoneCard, { props: { topic: 'Python Fundamentals', week: 1 } });
    expect(screen.getByText('Python Fundamentals')).toBeInTheDocument();
  });

  it('renders week pill', () => {
    render(MilestoneCard, { props: { topic: 'Test', week: 3 } });
    expect(screen.getByText('Week 3')).toBeInTheDocument();
  });

  it('shows "Complete" badge for complete status', () => {
    render(MilestoneCard, { props: { topic: 'Test', week: 1, status: 'complete' } });
    expect(screen.getByText(/Complete/)).toBeInTheDocument();
  });

  it('shows "In Progress" badge for current status', () => {
    render(MilestoneCard, { props: { topic: 'Test', week: 2, status: 'current' } });
    expect(screen.getByText(/In Progress/)).toBeInTheDocument();
  });

  it('shows "Upcoming" badge for pending status', () => {
    render(MilestoneCard, { props: { topic: 'Test', week: 4, status: 'pending' } });
    expect(screen.getByText(/Upcoming/)).toBeInTheDocument();
  });

  it('renders up to 5 subtopics', () => {
    const subtopics = ['A', 'B', 'C', 'D', 'E', 'F'];
    render(MilestoneCard, { props: { topic: 'T', week: 1, subtopics } });
    // Only 5 rendered (sliced)
    expect(screen.queryByText('F')).not.toBeInTheDocument();
    expect(screen.getByText('E')).toBeInTheDocument();
  });

  it('has aria-label with topic and week', () => {
    render(MilestoneCard, { props: { topic: 'React Basics', week: 2 } });
    expect(screen.getByRole('article', { name: /React Basics/ })).toBeInTheDocument();
  });
});
