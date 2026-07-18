import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import QuizOption from '../QuizOption.svelte';

const makeOption = (index = 0, text = 'Test option') => ({ index, text });

describe('QuizOption', () => {
  it('renders option text', () => {
    render(QuizOption, { props: { option: makeOption(0, 'Paris'), onSelect: vi.fn() } });
    expect(screen.getByText('Paris')).toBeInTheDocument();
  });

  it('renders correct letter pill (A for index 0)', () => {
    render(QuizOption, { props: { option: makeOption(0), onSelect: vi.fn() } });
    expect(screen.getByText('A')).toBeInTheDocument();
  });

  it('renders D for option index 3', () => {
    render(QuizOption, { props: { option: makeOption(3, 'Rome'), onSelect: vi.fn() } });
    expect(screen.getByText('D')).toBeInTheDocument();
  });

  it('button id matches quiz-option-{index}', () => {
    render(QuizOption, { props: { option: makeOption(2, 'Berlin'), onSelect: vi.fn() } });
    expect(document.getElementById('quiz-option-2')).toBeInTheDocument();
  });

  it('calls onSelect with correct index on click', async () => {
    const onSelect = vi.fn();
    render(QuizOption, { props: { option: makeOption(1, 'London'), onSelect } });
    await fireEvent.click(document.getElementById('quiz-option-1'));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it('aria-pressed is false when not selected', () => {
    render(QuizOption, { props: { option: makeOption(0), selected: false, onSelect: vi.fn() } });
    expect(document.getElementById('quiz-option-0')).toHaveAttribute('aria-pressed', 'false');
  });

  it('aria-pressed is true when selected', () => {
    render(QuizOption, { props: { option: makeOption(0), selected: true, onSelect: vi.fn() } });
    expect(document.getElementById('quiz-option-0')).toHaveAttribute('aria-pressed', 'true');
  });
});
