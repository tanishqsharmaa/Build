<script>
  /** @type {'complete' | 'current' | 'pending'} */
  export let status = 'pending';
  export let topic  = '';
  export let week   = 1;
  /** @type {string[]} */
  export let subtopics = [];
</script>

<article
  class="milestone-card"
  class:is-complete={status === 'complete'}
  class:is-current={status === 'current'}
  aria-label="Week {week}: {topic}"
>
  <header class="mc-header">
    <span class="week-pill">Week {week}</span>
    <span
      class="status-badge"
      class:badge-success={status === 'complete'}
      class:badge-accent={status === 'current'}
    >
      {status === 'complete' ? '✓ Complete' : status === 'current' ? '▶ In Progress' : '○ Upcoming'}
    </span>
  </header>

  <h3 class="mc-topic">{topic}</h3>

  {#if subtopics.length}
    <ul class="mc-subtopics">
      {#each subtopics.slice(0, 5) as sub}
        <li>{sub}</li>
      {/each}
    </ul>
  {/if}

  {#if status === 'current'}
    <div class="current-indicator" aria-hidden="true"></div>
  {/if}
</article>

<style>
  .milestone-card {
    position:       relative;
    background:     var(--color-surface);
    border:         1px solid var(--color-border);
    border-radius:  var(--radius);
    padding:        1.25rem 1.5rem;
    display:        flex;
    flex-direction: column;
    gap:            0.6rem;
    transition:     border-color 0.2s, box-shadow 0.2s;
    overflow:       hidden;
  }

  .is-current {
    border-color: var(--color-accent);
    box-shadow:   0 0 0 1px var(--color-accent),
                  0 8px 32px rgba(108, 71, 255, 0.2);
  }

  .is-complete {
    opacity: 0.7;
  }

  /* Glow strip on left edge for current */
  .current-indicator {
    position:      absolute;
    left:          0; top: 0; bottom: 0;
    width:         3px;
    background:    linear-gradient(180deg, #6c47ff, #00d4aa);
    border-radius: 3px 0 0 3px;
  }

  .mc-header {
    display:         flex;
    align-items:     center;
    justify-content: space-between;
    gap:             0.5rem;
  }

  .week-pill {
    font-size:     0.72rem;
    font-weight:   700;
    letter-spacing: 0.08em;
    color:         var(--color-muted);
    text-transform: uppercase;
  }

  .status-badge {
    display:       inline-flex;
    align-items:   center;
    padding:       0.2rem 0.65rem;
    border-radius: 100px;
    font-size:     0.72rem;
    font-weight:   600;
    border:        1px solid transparent;
  }

  /* badge-success and badge-accent come from app.css globals */
  :global(.status-badge.badge-success) {
    background: rgba(0, 212, 170, 0.1);
    color:      var(--color-accent2);
    border-color: rgba(0, 212, 170, 0.25);
  }
  :global(.status-badge.badge-accent) {
    background: rgba(108, 71, 255, 0.12);
    color:      #a78bfa;
    border-color: rgba(108, 71, 255, 0.3);
  }

  .mc-topic {
    font-size:   1rem;
    font-weight: 600;
    margin:      0;
    color:       var(--color-text);
    line-height: 1.3;
  }

  .mc-subtopics {
    margin:      0;
    padding:     0 0 0 1rem;
    list-style:  disc;
    display:     flex;
    flex-direction: column;
    gap:         0.25rem;
  }

  .mc-subtopics li {
    font-size:   0.82rem;
    color:       var(--color-muted);
    line-height: 1.4;
  }
</style>
