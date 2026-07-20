<svelte:head>
  <title>Quiz — SkillBridge</title>
  <meta name="description" content="Your daily adaptive knowledge quiz." />
</svelte:head>

<script>
  export const ssr = false;   // client-side only — quiz_id comes from URL param

  import { onMount }   from 'svelte';
  import { page }      from '$app/stores';
  import { goto }      from '$app/navigation';
  import QuizOption    from '$lib/components/QuizOption.svelte';

  const API_URL    = import.meta.env.VITE_API_URL;
  const TEST_UID   = import.meta.env.VITE_TEST_USER_ID;
  const TEST_EMAIL = import.meta.env.VITE_TEST_USER_EMAIL;

  let quizId    = '';
  let topic     = '';
  let questions = [];   // list of QuizQuestion objects
  let answers   = {};   // { questionIndex: selectedOptionIndex }
  let loading   = true;
  let fetchError = '';
  let submitting = false;

  $: answered    = Object.keys(answers).length;
  $: allAnswered = questions.length > 0 && answered === questions.length;
  $: progress    = questions.length ? Math.round((answered / questions.length) * 100) : 0;

  onMount(async () => {
    quizId = $page.url.searchParams.get('id') ?? '';
    if (!quizId) {
      goto('/dashboard');
      return;
    }

    try {
      const res = await fetch(`${API_URL}/quiz/${quizId}`);
      if (res.status === 404) {
        fetchError = 'Quiz not found. It may have expired or the link is incorrect.';
        loading = false;
        return;
      }
      if (!res.ok) {
        fetchError = `Failed to load quiz (${res.status}). Please try again.`;
        loading = false;
        return;
      }
      const data = await res.json();
      questions  = data.questions ?? [];
      topic      = data.topic     ?? 'Today\'s Quiz';
    } catch (e) {
      fetchError = `Network error: ${e.message}`;
    } finally {
      loading = false;
    }
  });

  function selectOption(questionIdx, optionIdx) {
    answers = { ...answers, [questionIdx]: optionIdx };
  }

  async function handleSubmit() {
    if (!allAnswered || submitting) return;
    submitting = true;

    const answerList = questions.map((_, i) => answers[i] ?? -1);

    try {
      const res = await fetch(`${API_URL}/quiz/submit`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          quiz_id:    quizId,
          user_id:    TEST_UID,
          user_email: TEST_EMAIL,
          answers:    answerList,
        }),
      });

      if (!res.ok) {
        const detail = await res.text().catch(() => '');
        fetchError = `Submission failed (${res.status}): ${detail}`;
        submitting = false;
        return;
      }

      const result = await res.json();
      // Pass result to results page via sessionStorage
      sessionStorage.setItem('quiz_result', JSON.stringify(result));
      goto(`/results?id=${quizId}`);
    } catch (e) {
      fetchError = `Submit error: ${e.message}`;
      submitting = false;
    }
  }
</script>

<div class="page">
  <div class="bg-orb" aria-hidden="true"></div>

  <div class="container">

    <!-- Back link -->
    <a href="/dashboard" class="back-link">← Dashboard</a>

    <!-- ── Loading ───────────────────────────────────────────────────── -->
    {#if loading}
      <div class="loading-state">
        <div class="spinner-lg" aria-label="Loading quiz..."></div>
        <p>Fetching your quiz…</p>
      </div>

    <!-- ── Error ─────────────────────────────────────────────────────── -->
    {:else if fetchError}
      <div class="error-card card">
        <div class="err-icon">⚠️</div>
        <h2>Something went wrong</h2>
        <p>{fetchError}</p>
        <a href="/dashboard" class="btn-primary">Back to Dashboard</a>
      </div>

    <!-- ── Quiz ──────────────────────────────────────────────────────── -->
    {:else}
      <!-- Header -->
      <header class="quiz-header">
        <div class="quiz-meta">
          <span class="badge badge-accent">Daily Quiz</span>
          <span class="quiz-topic">{topic}</span>
        </div>
        <span class="quiz-count">{answered} / {questions.length} answered</span>
      </header>

      <!-- Progress bar -->
      <div class="progress-track" role="progressbar" aria-valuenow={progress} aria-valuemax="100">
        <div class="progress-fill" style="width:{progress}%"></div>
      </div>

      <!-- Questions -->
      <div class="questions-list">
        {#each questions as q, qi}
          <div class="question-block card" id="question-{qi}">
            <p class="question-num">Question {qi + 1} of {questions.length}</p>
            <p class="question-text">{q.question}</p>
            <div class="options-list">
              {#each (q.options ?? []) as opt, oi}
                <QuizOption
                  option={{ index: oi, text: opt.text ?? opt }}
                  selected={answers[qi] === oi}
                  onSelect={(idx) => selectOption(qi, idx)}
                />
              {/each}
            </div>
          </div>
        {/each}
      </div>

      <!-- Submit -->
      <div class="submit-row">
        {#if !allAnswered}
          <p class="submit-hint">Answer all {questions.length} questions to submit.</p>
        {/if}
        <button
          id="quiz-submit-btn"
          class="btn-primary"
          disabled={!allAnswered || submitting}
          on:click={handleSubmit}
        >
          {#if submitting}
            <span class="spinner" aria-hidden="true"></span>
            Evaluating…
          {:else}
            Submit Quiz →
          {/if}
        </button>
      </div>

    {/if}
  </div>
</div>

<style>
  .page {
    min-height: 100vh;
    position:   relative;
    padding:    2rem 1.5rem 4rem;
  }

  .bg-orb {
    position:       fixed;
    width:          500px; height: 500px;
    background:     radial-gradient(circle, rgba(108,71,255,0.12) 0%, transparent 70%);
    border-radius:  50%;
    filter:         blur(90px);
    pointer-events: none;
    top: -150px; right: -100px;
    z-index: 0;
  }

  .container {
    position:       relative;
    z-index:        1;
    max-width:      680px;
    margin:         0 auto;
    display:        flex;
    flex-direction: column;
    gap:            1.5rem;
  }

  .back-link {
    color:           var(--color-muted);
    text-decoration: none;
    font-size:       0.9rem;
    width:           fit-content;
    transition:      color 0.2s;
  }
  .back-link:hover { color: var(--color-text); }

  /* Loading */
  .loading-state {
    display:         flex;
    flex-direction:  column;
    align-items:     center;
    gap:             1rem;
    padding:         4rem 0;
    color:           var(--color-muted);
    font-size:       0.95rem;
  }
  .spinner-lg {
    width:         40px; height: 40px;
    border:        3px solid rgba(255,255,255,0.1);
    border-top-color: var(--color-accent);
    border-radius: 50%;
    animation:     spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Error */
  .error-card {
    display:         flex;
    flex-direction:  column;
    align-items:     center;
    gap:             1rem;
    text-align:      center;
    padding:         3rem;
  }
  .err-icon { font-size: 2.5rem; }
  .error-card h2 { margin: 0; font-size: 1.3rem; }
  .error-card p  { margin: 0; color: var(--color-muted); }

  /* Quiz header */
  .quiz-header {
    display:         flex;
    align-items:     center;
    justify-content: space-between;
    flex-wrap:       wrap;
    gap:             0.75rem;
  }
  .quiz-meta { display: flex; align-items: center; gap: 0.75rem; }
  .quiz-topic {
    font-size:   1rem;
    font-weight: 600;
    color:       var(--color-text);
  }
  .quiz-count {
    font-size:   0.85rem;
    color:       var(--color-muted);
    white-space: nowrap;
  }

  /* Progress */
  .progress-track {
    height:        4px;
    background:    rgba(255,255,255,0.07);
    border-radius: 100px;
    overflow:      hidden;
  }
  .progress-fill {
    height:        100%;
    background:    var(--color-accent);
    border-radius: 100px;
    transition:    width 0.4s cubic-bezier(0.4,0,0.2,1);
  }

  /* Questions */
  .questions-list { display: flex; flex-direction: column; gap: 1.25rem; }
  .question-block { display: flex; flex-direction: column; gap: 1rem; }
  .question-num   { font-size: 0.75rem; color: var(--color-accent); font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin: 0; }
  .question-text  { font-size: 1.05rem; font-weight: 600; line-height: 1.5; margin: 0; }
  .options-list   { display: flex; flex-direction: column; gap: 0.6rem; }

  /* Submit */
  .submit-row {
    display:     flex;
    flex-direction: column;
    align-items: center;
    gap:         0.75rem;
    padding-top: 0.5rem;
  }
  .submit-hint { font-size: 0.82rem; color: var(--color-muted); margin: 0; }
</style>
