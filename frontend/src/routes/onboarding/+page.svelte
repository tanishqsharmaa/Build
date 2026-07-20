<svelte:head>
  <title>Get Started — SkillBridge</title>
  <meta name="description" content="Tell us your target role and current skills to generate your personalized learning plan." />
</svelte:head>

<script>
  import { enhance } from '$app/forms';

  let { form } = $props(); // populated by SvelteKit on action error

  let goal        = $state('');
  let userEmail   = $state('');
  let skillInput  = $state('');
  let skills      = $state([]);
  let hours       = $state(15);
  let loading     = $state(false);

  /** Add skill on Enter or comma */
  function handleSkillKey(e) {
    const raw = skillInput.trim().replace(/,$/, '');
    if ((e.key === 'Enter' || e.key === ',') && raw) {
      e.preventDefault();
      if (!skills.includes(raw)) skills = [...skills, raw];
      skillInput = '';
    }
  }

  function removeSkill(s) {
    skills = skills.filter(sk => sk !== s);
  }

  let canSubmit = $derived(goal.trim().length > 0 && userEmail.trim().length > 0 && (skills.length > 0 || skillInput.trim().length > 0) && !loading);
</script>

<div class="page">
  <!-- Background orbs -->
  <div class="bg-orb orb-1" aria-hidden="true"></div>
  <div class="bg-orb orb-2" aria-hidden="true"></div>

  <div class="container">
    <!-- Header -->
    <a href="/" class="back-link">← Back</a>

    <header class="page-header">
      <span class="badge badge-accent">Step 1 of 1</span>
      <h1>Tell us about yourself</h1>
      <p class="subtitle">
        We'll analyze your skill gap against real Indian job-market data and build a personalized learning plan.
      </p>
    </header>

    <!-- Error from server action -->
    {#if form?.error}
      <div class="error-banner" role="alert">
        ⚠️ {form.error}
      </div>
    {/if}

    <!-- Form -->
    <form
      method="POST"
      use:enhance={() => {
        loading = true;
        return async ({ update }) => {
          loading = false;
          await update();
        };
      }}
      class="form-card card"
    >
      <!-- Hidden: comma-joined skills list -->
<input type="hidden" name="skills" value={skillInput.trim() ? [...skills, skillInput.trim()].join(',') : skills.join(',')} />

      <!-- Goal -->
      <div class="field">
        <label for="user_goal" class="field-label">
          What role are you targeting?
          <span class="required" aria-hidden="true">*</span>
        </label>
        <input
          id="user_goal"
          name="user_goal"
          type="text"
          class="field-input"
          placeholder="e.g. Backend Developer, Data Analyst, ML Engineer"
          bind:value={goal}
          required
          autocomplete="off"
        />
      </div>

      <!-- Email -->
      <div class="field">
        <label for="user_email" class="field-label">
          Your email
          <span class="required" aria-hidden="true">*</span>
        </label>
        <input
          id="user_email"
          name="user_email"
          type="email"
          class="field-input"
          placeholder="you@example.com"
          bind:value={userEmail}
          required
          autocomplete="email"
        />
        <p class="field-hint">We'll send your morning brief and daily quiz link here.</p>
      </div>

      <!-- Skills chips -->
      <div class="field">
        <label for="skill_input" class="field-label">
          Your current skills
          <span class="required" aria-hidden="true">*</span>
        </label>
        <div class="chips-wrapper" class:focused={false}>
          {#each skills as s}
            <span class="chip">
              {s}
              <button
                type="button"
                class="chip-remove"
                onclick={() => removeSkill(s)}
                aria-label="Remove {s}"
              >×</button>
            </span>
          {/each}
          <input
            id="skill_input"
            class="chip-input"
            bind:value={skillInput}
            onkeydown={handleSkillKey}
            placeholder={skills.length ? 'Add more...' : 'Type a skill, press Enter to add'}
            autocomplete="off"
          />
        </div>
        <p class="field-hint">e.g. Python · SQL · React · Machine Learning · Java</p>
      </div>

      <!-- Hours per week slider -->
      <div class="field">
        <label for="hours" class="field-label">
          Hours per week for learning
        </label>
        <div class="slider-row">
          <span class="slider-min">5h</span>
          <input
            id="hours"
            name="hours"
            type="range"
            class="slider"
            min="5"
            max="40"
            step="5"
            bind:value={hours}
          />
          <span class="slider-max">40h</span>
          <span class="slider-value">{hours} h/week</span>
        </div>
      </div>

      <!-- Submit -->
      <button
        type="submit"
        class="btn-primary btn-full"
        disabled={!canSubmit}
        id="onboarding-submit"
      >
        {#if loading}
          <span class="spinner" aria-hidden="true"></span>
          Analyzing your skills… (15–30 sec)
        {:else}
          Analyze My Skills &amp; Build My Plan →
        {/if}
      </button>

      {#if loading}
        <p class="loading-note" role="status">
          ⚡ Running AI agents in sequence — skill gap analysis, then learning plan generation.
          Please keep this tab open.
        </p>
      {/if}
    </form>
  </div>
</div>

<style>
  .page {
    min-height:      100vh;
    display:         flex;
    align-items:     center;
    justify-content: center;
    padding:         2rem;
    position:        relative;
    overflow:        hidden;
  }

  .bg-orb {
    position:      absolute;
    border-radius: 50%;
    filter:        blur(80px);
    pointer-events: none;
  }
  .orb-1 {
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(108,71,255,0.18) 0%, transparent 70%);
    top: -200px; right: -150px;
  }
  .orb-2 {
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(0,212,170,0.10) 0%, transparent 70%);
    bottom: -150px; left: -100px;
  }

  .container {
    position:       relative;
    width:          100%;
    max-width:      560px;
    display:        flex;
    flex-direction: column;
    gap:            1.5rem;
  }

  .back-link {
    color:           var(--color-muted);
    text-decoration: none;
    font-size:       0.9rem;
    transition:      color 0.2s;
    width:           fit-content;
  }
  .back-link:hover { color: var(--color-text); }

  .page-header { display: flex; flex-direction: column; gap: 0.75rem; }
  .page-header h1 {
    font-size:      2rem;
    font-weight:    800;
    margin:         0;
    letter-spacing: -0.02em;
  }
  .subtitle {
    color:       var(--color-muted);
    font-size:   0.95rem;
    line-height: 1.65;
    margin:      0;
  }

  .error-banner {
    background:    rgba(255, 77, 109, 0.1);
    border:        1px solid rgba(255, 77, 109, 0.3);
    border-radius: var(--radius-sm);
    padding:       0.85rem 1rem;
    font-size:     0.9rem;
    color:         #ff8099;
  }

  .form-card { display: flex; flex-direction: column; gap: 1.5rem; }

  /* Field */
  .field { display: flex; flex-direction: column; gap: 0.5rem; }
  .field-label {
    font-size:   0.88rem;
    font-weight: 600;
    color:       var(--color-text);
  }
  .required { color: var(--color-accent); margin-left: 0.2rem; }
  .field-input {
    width:         100%;
    padding:       0.75rem 1rem;
    background:    var(--color-surface-2);
    border:        1px solid var(--color-border);
    border-radius: var(--radius-sm);
    color:         var(--color-text);
    font-size:     0.95rem;
    font-family:   inherit;
    outline:       none;
    transition:    border-color 0.2s;
  }
  .field-input:focus { border-color: var(--color-accent); }
  .field-hint { font-size: 0.78rem; color: var(--color-muted); margin: 0; }

  /* Chips input */
  .chips-wrapper {
    display:       flex;
    flex-wrap:     wrap;
    gap:           0.4rem;
    padding:       0.6rem 0.75rem;
    background:    var(--color-surface-2);
    border:        1px solid var(--color-border);
    border-radius: var(--radius-sm);
    min-height:    48px;
    cursor:        text;
    transition:    border-color 0.2s;
  }
  .chips-wrapper:focus-within { border-color: var(--color-accent); }

  .chip {
    display:       inline-flex;
    align-items:   center;
    gap:           0.3rem;
    padding:       0.2rem 0.5rem 0.2rem 0.65rem;
    background:    rgba(108, 71, 255, 0.15);
    color:         #a78bfa;
    border:        1px solid rgba(108, 71, 255, 0.3);
    border-radius: 100px;
    font-size:     0.82rem;
    font-weight:   500;
  }
  .chip-remove {
    background:  none;
    border:      none;
    color:       inherit;
    cursor:      pointer;
    font-size:   1rem;
    line-height: 1;
    padding:     0;
    opacity:     0.7;
    transition:  opacity 0.15s;
  }
  .chip-remove:hover { opacity: 1; }

  .chip-input {
    flex:        1;
    min-width:   120px;
    background:  none;
    border:      none;
    color:       var(--color-text);
    font-size:   0.9rem;
    font-family: inherit;
    outline:     none;
    padding:     0.1rem 0;
  }
  .chip-input::placeholder { color: var(--color-muted); }

  /* Slider */
  .slider-row {
    display:     flex;
    align-items: center;
    gap:         0.75rem;
  }
  .slider-min, .slider-max {
    font-size: 0.78rem;
    color:     var(--color-muted);
    flex-shrink: 0;
  }
  .slider {
    flex:        1;
    accent-color: var(--color-accent);
    cursor:      pointer;
    height:      4px;
  }
  .slider-value {
    font-size:   0.88rem;
    font-weight: 700;
    color:       var(--color-accent);
    min-width:   60px;
    text-align:  right;
  }

  /* Loading note */
  .loading-note {
    font-size:   0.82rem;
    color:       var(--color-muted);
    text-align:  center;
    margin:      0;
    line-height: 1.6;
  }
</style>
