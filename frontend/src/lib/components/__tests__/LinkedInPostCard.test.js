import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import LinkedInPostCard from '../LinkedInPostCard.svelte';

describe('LinkedInPostCard', () => {
  it('renders post text', () => {
    render(LinkedInPostCard, { props: { postText: 'Hello LinkedIn!' } });
    expect(screen.getByText('Hello LinkedIn!')).toBeInTheDocument();
  });

  it('renders default placeholder text when no postText provided', () => {
    render(LinkedInPostCard, {});
    expect(screen.getByText(/Complete your first quiz/)).toBeInTheDocument();
  });

  it('copy button has correct id', () => {
    render(LinkedInPostCard, { props: { postText: 'Test post' } });
    expect(document.getElementById('copy-linkedin-post')).toBeInTheDocument();
  });

  it('copy button is rendered with "Copy Post" label', () => {
    render(LinkedInPostCard, { props: { postText: 'Test' } });
    expect(screen.getByText(/Copy Post/)).toBeInTheDocument();
  });

  it('calls clipboard API on copy button click', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    render(LinkedInPostCard, { props: { postText: 'My great post' } });
    await fireEvent.click(document.getElementById('copy-linkedin-post'));

    expect(writeText).toHaveBeenCalledWith('My great post');
  });
});
