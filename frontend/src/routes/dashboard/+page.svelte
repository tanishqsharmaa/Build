<svelte:head>
  <title>Dashboard — SkillBridge</title>
  <meta name="description" content="Your personalized learning milestones, quiz scores, and weekly LinkedIn post." />
</svelte:head>

<script>
  import MilestoneCard    from '$lib/components/MilestoneCard.svelte';
  import ProgressBar      from '$lib/components/ProgressBar.svelte';
  import LinkedInPostCard from '$lib/components/LinkedInPostCard.svelte';

  export let data; // { plan, scores, userId }

  $: milestones  = data.plan?.milestones            ?? [];
  $: currentIdx  = data.plan?.current_milestone_index ?? 0;
  $: revCount    = data.plan?.plan_revision_count    ?? 0;
  $: totalWeeks  = milestones.length;
  $: scores      = data.scores ?? [];

  function getMilestoneStatus(idx) {
    if (idx < currentIdx)  return 'complete';
    if (idx === currentIdx) return 'current';
    return 'pending';
  }

  function formatDate(iso) {
    return new Date(iso).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
  }
</script>

<div class="page">
  <!-- Subtle bg orbs -->
  <div class="bg-orb orb-1" aria-hidden="true"></div>

  <div class="container">

    <!-- ── Top Nav ──────────────────────────────────────────────────── -->
    <nav class="top-nav">
      <a href="/" class="nav-logo">
        <span>⚡</span><span>SkillBridge</span>
      </a>
      <a href="/onboarding" class="btn-secondary nav-action">+ New Plan</a>
    </nav>

    <!-- ── Header ───────────────────────────────────────────────────── -->
    <header class="dash-header">
      <div class="header-left">
        <h1>Your Learning Dashboard</h1>
        {#if data.plan}
          <p class="header-sub">
            Week {currentIdx + 1} of {totalWeeks}
            {#if revCount > 0}
              · <span class="rev-count">Plan revised {revCount}×</span>
            {/if}
          </p>
        {:else}
          <p class="header-sub">No active plan yet. Complete onboarding to get started.</p>
        {/if}
      </div>

      {#if data.plan && scores.length > 0}
        {@const avg = Math.round(scores.reduce((s, r) => s + (r.overall_score ?? 0), 0) / scores.length)}
        <div class="readiness-pill" class:good={avg >= 70} class:warn={avg < 70}>
          <span class="readiness-num">{avg}%</span>
          <span class="readiness-label">avg score</span>
        </div>
      {/if}
    </header>

    <!-- ── Empty state ──────────────────────────────────────────────── -->
    {#if !data.plan}
      <div class="empty-state card">
        <div class="empty-icon">🗺️</div>
        <h2>No active learning plan found</h2>
        <p>Fill in the onboarding form and we'll build your personalized plan in seconds.</p>
        <a href="/onboarding" class="btn-primary" id="empty-start-btn">Get Started →</a>
      </div>

    {:else}

      <!-- ── Milestone Timeline ──────────────────────────────────────── -->
      <section class="section">
        <h2 class="section-title">Milestone Timeline</h2>
        <div class="milestones-grid">
          {#each milestones as m, i}
            <MilestoneCard
              topic={m.topic ?? m.milestone_id ?? `Week ${i + 1}`}
              week={m.week ?? i + 1}
              status={getMilestoneStatus(i)}
              subtopics={m.daily_subtopics ?? []}
            />
          {/each}
        </div>
      </section>

      <!-- ── Score History ───────────────────────────────────────────── -->
      <section class="section">
        <h2 class="section-title">Quiz Score History</h2>

        {#if scores.length === 0}
          <div class="card no-scores">
            <p>No quiz scores yet — your first quiz will be emailed at 4:00 PM IST today.</p>
          </div>
        {:else}
          <div class="scores-card card">
            {#each scores as s, i}
              <ProgressBar
                label={formatDate(s.created_at)}
                score={Math.round(s.overall_score ?? 0)}
              />
              {#if i < scores.length - 1}
                <div class="score-divider"></div>
              {/if}
            {/each}
          </div>
        {/if}
      </section>

      <!-- ── LinkedIn Post ──────────────────────────────────────────── -->
      <section class="section">
        <h2 class="section-title">Weekly LinkedIn Post</h2>
        <LinkedInPostCard
          postText={scores.length > 0
            ? "🚀 Just completed another week of AI-powered learning with SkillBridge! My quiz average is improving and I'm making real progress toward my goal. #LearningJourney #SDG4 #AILearning"
            : undefined}
        />
        <p class="li-note">Full AI-generated post appears after Agent 4 is enabled (Sprint 8).</p>
      </section>

    {/if}
  </div>
</div>

<style>
  .page {
    min-height: 100vh;
    position:   relative;
    overflow-x: hidden;
    padding-bottom: 4rem;
  }

  .bg-orb {
    position:       fixed;
    border-radius:  50%;
    filter:         blur(100px);
    pointer-events: none;
    z-index:        0;
  }
  .orb-1 {
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(108,71,255,0.12) 0%, transparent 70%);
    top: 0; left: 50%; transform: translateX(-50%);
  }

  .container {
    position:   relative;
    z-index:    1;
    max-width:  1000px;
    margin:     0 auto;
    padding:    0 1.5rem;
    display:    flex;
    flex-direction: column;
    gap:        2rem;
  }

  /* Nav */
  .top-nav {
    display:         flex;
    align-items:     center;
    justify-content: space-between;
    padding:         1.5rem 0;
    border-bottom:   1px solid var(--color-border);
  }
  .nav-logo {
    display:         flex;
    align-items:     center;
    gap:             0.4rem;
    font-size:       1.15rem;
    font-weight:     700;
    color:           var(--color-text);
    text-decoration: none;
  }
  .nav-action {
    font-size:   0.88rem;
    padding:     0.5rem 1.1rem;
  }

  /* Header */
  .dash-header {
    display:         flex;
    align-items:     flex-start;
    justify-content: space-between;
    gap:             1rem;
    flex-wrap:       wrap;
  }
  .dash-header h1 {
    font-size:      1.8rem;
    font-weight:    800;
    margin:         0;
    letter-spacing: -0.02em;
  }
  .header-sub {
    font-size:   0.92rem;
    color:       var(--color-muted);
    margin:      0.25rem 0 0;
  }
  .rev-count { color: var(--color-warning); }

  .readiness-pill {
    display:         flex;
    flex-direction:  column;
    align-items:     center;
    padding:         0.75rem 1.25rem;
    border-radius:   var(--radius);
    border:          1px solid var(--color-border);
    background:      var(--color-surface);
    min-width:       80px;
  }
  .readiness-pill.good { border-color: rgba(0,212,170,0.35); }
  .readiness-pill.warn { border-color: rgba(245,158,11,0.35); }
  .readiness-num  { font-size: 1.5rem; font-weight: 800; }
  .good .readiness-num { color: var(--color-accent2); }
  .warn .readiness-num { color: var(--color-warning); }
  .readiness-label { font-size: 0.72rem; color: var(--color-muted); text-transform: uppercase; letter-spacing: 0.06em; }

  /* Section */
  .section { display: flex; flex-direction: column; gap: 1rem; }
  .section-title {
    font-size:   1.1rem;
    font-weight: 700;
    margin:      0;
  }

  /* Empty state */
  .empty-state {
    display:         flex;
    flex-direction:  column;
    align-items:     center;
    gap:             1rem;
    text-align:      center;
    padding:         3rem 2rem;
  }
  .empty-icon { font-size: 3rem; }
  .empty-state h2 { font-size: 1.3rem; font-weight: 700; margin: 0; }
  .empty-state p  { color: var(--color-muted); margin: 0; }

  /* Milestones */
  .milestones-grid {
    display:               grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap:                   1rem;
  }

  /* Scores */
  .scores-card {
    display:        flex;
    flex-direction: column;
    gap:            0.85rem;
  }
  .score-divider {
    height:     1px;
    background: var(--color-border);
  }
  .no-scores {
    color:       var(--color-muted);
    font-size:   0.9rem;
    text-align:  center;
    padding:     1.5rem;
  }
  .no-scores p { margin: 0; }

  /* LinkedIn note */
  .li-note {
    font-size: 0.78rem;
    color:     var(--color-muted);
    margin:    0;
  }
</style>
