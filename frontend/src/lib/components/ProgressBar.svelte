<script>
  /** 0–100 */
  export let score = 0;
  export let label = '';
</script>

<div class="progress-row">
  {#if label}
    <span class="progress-label">{label}</span>
  {/if}

  <div class="track" role="progressbar" aria-valuenow={score} aria-valuemin="0" aria-valuemax="100">
    <div
      class="fill"
      style="width:{score}%; background:{score >= 70 ? 'var(--color-accent2)' : 'var(--color-warning)'};"
    ></div>
  </div>

  <span class="score-text" style="color:{score >= 70 ? 'var(--color-accent2)' : 'var(--color-warning)'}">
    {score}%
  </span>
</div>

<style>
  .progress-row {
    display:     flex;
    align-items: center;
    gap:         0.75rem;
  }

  .progress-label {
    font-size:   0.78rem;
    color:       var(--color-muted);
    min-width:   80px;
    white-space: nowrap;
    overflow:    hidden;
    text-overflow: ellipsis;
  }

  .track {
    flex:          1;
    height:        6px;
    background:    rgba(255, 255, 255, 0.08);
    border-radius: 100px;
    overflow:      hidden;
  }

  .fill {
    height:        100%;
    border-radius: 100px;
    transition:    width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .score-text {
    font-size:   0.82rem;
    font-weight: 600;
    min-width:   38px;
    text-align:  right;
  }
</style>
