<svelte:head>
  <title>Results — SkillBridge</title>
  <meta name="description" content="Your quiz result and personalized feedback." />
</svelte:head>

<script>
  import { onMount }  from 'svelte';
  import { goto }     from '$app/navigation';

  let result        = null;
  let score         = 0;
  let animatedScore = 0;
  let expanded      = {};   // { questionIndex: boolean } for accordion

  // SVG ring constants
  const R = 54;
  const C = 2 * Math.PI * R;  // circumference ≈ 339.3
  $: dash = C - (animatedScore / 100) * C;
  $: ringColor = result?.recommendation === 'advance' ? '#00d4aa' : '#f59e0b';

  onMount(() => {
    const raw = sessionStorage.getItem('quiz_result');
    if (!raw) { goto('/dashboard'); return; }

    result = JSON.parse(raw);
    score  = Math.round(result.overall_score ?? 0);

    // Animate counter
    let current = 0;
    const step = () => {
      current += 2;
      animatedScore = Math.min(current, score);
      if (current < score) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });

  function toggleFeedback(i) {
    expanded = { ...expanded, [i]: !expanded[i] };
  }
</script>

<div class="page">
  <div class="bg-orb" aria-hidden="true"></div>

  <div class="container">
    <a href="/dashboard" class="back-link">← Dashboard</a>

    {#if result}
      <!-- ── Score Ring ────────────────────────────────────────────── -->
      <div class="score-section">
        <svg
          class="score-ring"
          width="160" height="160"
          viewBox="0 0 140 140"
          aria-label="Score: {score}%"
          role="img"
        >
          <!-- Track -->
          <circle cx="70" cy="70" r={R}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            stroke-width="12"
          />
          <!-- Fill -->
          <circle cx="70" cy="70" r={R}
            fill="none"
            stroke={ringColor}
            stroke-width="12"
            stroke-dasharray={C}
            stroke-dashoffset={dash}
            stroke-linecap="round"
            transform="rotate(-90 70 70)"
            style="transition: stroke-dashoffset 0.05s linear, stroke 0.3s ease"
          />
          <!-- Score label -->
          <text x="70" y="65" text-anchor="middle" font-size="26" font-weight="800" fill="white" font-family="Inter, sans-serif">
            {animatedScore}%
          </text>
          <text x="70" y="84" text-anchor="middle" font-size="11" fill="rgba(240,240,245,0.5)" font-family="Inter, sans-serif">
            score
          </text>
        </svg>

        <!-- Banner -->
        <div
          class="result-banner"
          class:advance={result.recommendation === 'advance'}
          class:review={result.recommendation === 'review'}
        >
          {#if result.recommendation === 'advance'}
            🎉 Great work! You advance to the next milestone.
          {:else}
            🔄 Keep going! Your plan has been updated to help you improve.
          {/if}
        </div>

        {#if result.summary_feedback}
          <p class="summary-feedback">{result.summary_feedback}</p>
        {/if}
      </div>

      <!-- ── Per-Question Feedback ──────────────────────────────────── -->
      {#if result.per_question?.length}
        <section class="feedback-section">
          <h2 class="section-title">Question Breakdown</h2>
          <div class="feedback-list">
            {#each result.per_question as pq, i}
              <div class="feedback-item card" class:correct={pq.correct} class:wrong={!pq.correct}>
                <button
                  class="feedback-toggle"
                  on:click={() => toggleFeedback(i)}
                  aria-expanded={!!expanded[i]}
                >
                  <span class="q-result-icon">{pq.correct ? '✓' : '✗'}</span>
                  <span class="q-label">Question {i + 1}</span>
                  <span class="q-status">{pq.correct ? 'Correct' : 'Incorrect'}</span>
                  <span class="q-chevron">{expanded[i] ? '▲' : '▼'}</span>
                </button>

                {#if expanded[i] && pq.feedback}
                  <div class="feedback-detail">
                    <p>{pq.feedback}</p>
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        </section>
      {/if}

      <!-- ── CTA ───────────────────────────────────────────────────── -->
      <div class="cta-row">
        <a href="/dashboard" class="btn-primary" id="results-back-btn">
          Back to Dashboard →
        </a>
      </div>

    {:else}
      <!-- Loading state while sessionStorage is read -->
      <div class="loading-state">
        <div class="spinner-lg"></div>
        <p>Loading your results…</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .page {
    min-height: 100vh;
    padding:    2rem 1.5rem 4rem;
    position:   relative;
  }
  .bg-orb {
    position:       fixed;
    width:          500px; height: 500px;
    background:     radial-gradient(circle, rgba(0,212,170,0.10) 0%, transparent 70%);
    border-radius:  50%;
    filter:         blur(90px);
    pointer-events: none;
    bottom: -100px; left: -100px;
    z-index: 0;
  }
  .container {
    position:       relative;
    z-index:        1;
    max-width:      620px;
    margin:         0 auto;
    display:        flex;
    flex-direction: column;
    gap:            2rem;
  }
  .back-link {
    color:           var(--color-muted);
    text-decoration: none;
    font-size:       0.9rem;
    width:           fit-content;
    transition:      color 0.2s;
  }
  .back-link:hover { color: var(--color-text); }

  /* Score section */
  .score-section {
    display:         flex;
    flex-direction:  column;
    align-items:     center;
    gap:             1.25rem;
    text-align:      center;
    padding:         2rem 0 0.5rem;
  }
  .score-ring { filter: drop-shadow(0 0 20px rgba(0,212,170,0.2)); }

  .result-banner {
    padding:       0.75rem 1.75rem;
    border-radius: var(--radius-lg);
    font-size:     0.95rem;
    font-weight:   600;
    border:        1px solid transparent;
  }
  .result-banner.advance {
    background:   rgba(0, 212, 170, 0.1);
    color:        var(--color-accent2);
    border-color: rgba(0, 212, 170, 0.25);
  }
  .result-banner.review {
    background:   rgba(245, 158, 11, 0.1);
    color:        var(--color-warning);
    border-color: rgba(245, 158, 11, 0.25);
  }

  .summary-feedback {
    font-size:   0.92rem;
    color:       var(--color-muted);
    line-height: 1.7;
    max-width:   460px;
    margin:      0;
  }

  /* Feedback accordion */
  .section-title { font-size: 1.1rem; font-weight: 700; margin: 0; }
  .feedback-section { display: flex; flex-direction: column; gap: 0.75rem; }
  .feedback-list    { display: flex; flex-direction: column; gap: 0.5rem; }

  .feedback-item {
    padding: 0;
    overflow: hidden;
  }
  .feedback-item.correct { border-color: rgba(0,212,170,0.25); }
  .feedback-item.wrong   { border-color: rgba(255,77,109,0.25); }

  .feedback-toggle {
    width:           100%;
    display:         flex;
    align-items:     center;
    gap:             0.75rem;
    padding:         0.9rem 1.25rem;
    background:      none;
    border:          none;
    color:           var(--color-text);
    font-family:     inherit;
    font-size:       0.9rem;
    cursor:          pointer;
    text-align:      left;
  }
  .feedback-toggle:hover { background: rgba(255,255,255,0.03); }

  .q-result-icon {
    font-size:   1rem;
    font-weight: 700;
    width:       20px;
  }
  .correct .q-result-icon { color: var(--color-accent2); }
  .wrong   .q-result-icon { color: var(--color-danger); }

  .q-label  { flex: 1; font-weight: 600; }
  .q-status { font-size: 0.78rem; color: var(--color-muted); }
  .q-chevron { font-size: 0.7rem; color: var(--color-muted); }

  .feedback-detail {
    padding: 0 1.25rem 1rem;
    border-top: 1px solid var(--color-border);
  }
  .feedback-detail p {
    font-size:   0.88rem;
    color:       var(--color-muted);
    line-height: 1.65;
    margin:      0.75rem 0 0;
  }

  /* CTA */
  .cta-row { display: flex; justify-content: center; }

  /* Loading */
  .loading-state {
    display:         flex;
    flex-direction:  column;
    align-items:     center;
    gap:             1rem;
    padding:         4rem 0;
    color:           var(--color-muted);
  }
  .spinner-lg {
    width:         40px; height: 40px;
    border:        3px solid rgba(255,255,255,0.1);
    border-top-color: var(--color-accent);
    border-radius: 50%;
    animation:     spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
