<script>
  export let postText = 'Complete your first quiz to unlock your AI-generated LinkedIn post!';

  let copied = false;

  async function copy() {
    try {
      await navigator.clipboard.writeText(postText);
      copied = true;
      setTimeout(() => (copied = false), 2000);
    } catch {
      // Clipboard not available (non-HTTPS dev) — fallback
      const el = document.createElement('textarea');
      el.value = postText;
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
      copied = true;
      setTimeout(() => (copied = false), 2000);
    }
  }
</script>

<div class="linkedin-card">
  <div class="li-header">
    <div class="li-logo" aria-hidden="true">in</div>
    <span class="li-label">AI-Generated LinkedIn Post</span>
    <span class="li-badge">Weekly</span>
  </div>

  <p class="li-text">{postText}</p>

  <button
    id="copy-linkedin-post"
    class="li-copy-btn"
    on:click={copy}
    aria-label="Copy LinkedIn post to clipboard"
  >
    {#if copied}
      <span>✓</span> Copied!
    {:else}
      <span>📋</span> Copy Post
    {/if}
  </button>
</div>

<style>
  .linkedin-card {
    --color-linkedin:       #0077b5;
    --color-linkedin-light: #4fa8d5;
    background:    var(--color-surface);
    border:        1px solid var(--color-border);
    border-radius: var(--radius);
    padding:       1.5rem;
    display:       flex;
    flex-direction: column;
    gap:           1rem;
    transition:    border-color 0.2s;
  }
  .linkedin-card:hover {
    border-color: color-mix(in srgb, var(--color-linkedin) 40%, transparent);
  }

  .li-header {
    display:     flex;
    align-items: center;
    gap:         0.6rem;
  }

  .li-logo {
    width:           30px;
    height:          30px;
    background:      var(--color-linkedin);
    border-radius:   6px;
    display:         flex;
    align-items:     center;
    justify-content: center;
    font-size:       0.82rem;
    font-weight:     800;
    color:           white;
    flex-shrink:     0;
  }

  .li-label {
    font-size:   0.85rem;
    font-weight: 600;
    color:       var(--color-text);
    flex:        1;
  }

  .li-badge {
    font-size:     0.7rem;
    font-weight:   600;
    padding:       0.15rem 0.5rem;
    background:    color-mix(in srgb, var(--color-linkedin) 12%, transparent);
    color:         var(--color-linkedin-light);
    border-radius: 100px;
    border:        1px solid color-mix(in srgb, var(--color-linkedin) 20%, transparent);
  }

  .li-text {
    font-size:   0.92rem;
    color:       var(--color-muted);
    line-height: 1.7;
    margin:      0;
    white-space: pre-wrap;
    font-style:  italic;
  }

  .li-copy-btn {
    display:         inline-flex;
    align-items:     center;
    justify-content: center;
    gap:             0.4rem;
    padding:         0.6rem 1.25rem;
    background:      color-mix(in srgb, var(--color-linkedin) 10%, transparent);
    color:           var(--color-linkedin-light);
    border:          1px solid color-mix(in srgb, var(--color-linkedin) 25%, transparent);
    border-radius:   var(--radius-sm);
    font-size:       0.88rem;
    font-weight:     600;
    cursor:          pointer;
    font-family:     inherit;
    align-self:      flex-start;
    transition:      background 0.2s, transform 0.15s;
  }
  .li-copy-btn:hover {
    background: color-mix(in srgb, var(--color-linkedin) 20%, transparent);
    transform:  translateY(-1px);
  }
  .li-copy-btn:active {
    transform: translateY(0);
  }
</style>
