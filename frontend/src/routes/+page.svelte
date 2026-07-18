<svelte:head>
  <title>SkillBridge — AI-Powered Skill Gap Analyzer</title>
  <meta
    name="description"
    content="SkillBridge uses multi-agent AI to analyze your skill gaps against Indian job market data,
    build a personalized weekly learning plan, and quiz you every day until you're job-ready."
  />
  <meta property="og:title" content="SkillBridge — AI-Powered Skill Gap Analyzer" />
  <meta property="og:description" content="Bridge the skill gap. Land the job." />
</svelte:head>

<main class="root">
  <!-- Ambient gradient orbs -->
  <div class="bg-mesh" aria-hidden="true">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
  </div>

  <!-- Nav -->
  <nav class="nav">
    <div class="nav-logo">
      <span aria-hidden="true">⚡</span>
      <span>SkillBridge</span>
    </div>
    <div class="nav-links">
      <a
        href="https://github.com/tanishqsharmaa/Build"
        target="_blank"
        rel="noopener noreferrer"
        class="nav-link"
      >GitHub ↗</a>
    </div>
  </nav>

  <!-- ── Hero ─────────────────────────────────────────────────────────────── -->
  <section class="hero">
    <div class="hero-content">
      <span class="badge badge-accent anim" style="animation-delay:0.1s">
        🎓 SDG 4 · Quality Education · IBM SkillsBuild 2026
      </span>

      <h1 class="headline anim" style="animation-delay:0.2s">
        Bridge the Gap.<br />
        <span class="gradient-text">Land the Job.</span>
      </h1>

      <p class="subhead anim" style="animation-delay:0.3s">
        Multi-agent AI analyzes your skill gaps against real Indian job-market data,
        builds a week-by-week learning plan, and sends you a quiz every day —
        adapting automatically when you struggle.
      </p>

      <div class="stats-row anim" style="animation-delay:0.4s">
        <div class="stat"><span>🤖</span><span>5 AI Agents</span></div>
        <div class="stat-sep"></div>
        <div class="stat"><span>📊</span><span>121 Job Roles</span></div>
        <div class="stat-sep"></div>
        <div class="stat"><span>📅</span><span>Daily Adaptive Quizzes</span></div>
      </div>

      <div class="cta-row anim" style="animation-delay:0.5s">
        <a href="/onboarding" id="cta-start" class="btn-primary btn-hero">
          Start Your Journey →
        </a>
        <a href="#how" class="btn-secondary btn-hero">See How It Works</a>
      </div>
    </div>
  </section>

  <!-- ── How It Works ──────────────────────────────────────────────────────── -->
  <section class="how" id="how">
    <h2>How SkillBridge Works</h2>

    <div class="steps-grid">
      <article class="card card-hover step-card">
        <div class="step-num">01</div>
        <div class="step-icon">🔍</div>
        <h3>Skill Gap Analysis</h3>
        <p>
          Agent 1 uses RAG over 121 job-role embeddings to pinpoint exactly which
          skills you're missing — and by how much.
        </p>
      </article>

      <article class="card card-hover step-card">
        <div class="step-num">02</div>
        <div class="step-icon">🗓️</div>
        <h3>Personalized Plan</h3>
        <p>
          Agent 2 generates a week-by-week milestone plan with free resources
          from YouTube, GitHub, and Coursera.
        </p>
      </article>

      <article class="card card-hover step-card">
        <div class="step-num">03</div>
        <div class="step-icon">☀️</div>
        <h3>Daily Morning Brief</h3>
        <p>
          Every morning at 7:30 AM, Agent 3a emails a concise cheat sheet — key
          concepts, a mnemonic, and 3 think-about questions.
        </p>
      </article>

      <article class="card card-hover step-card">
        <div class="step-num">04</div>
        <div class="step-icon">✏️</div>
        <h3>Adaptive Quizzes</h3>
        <p>
          At 4 PM, Agent 3b sends a 5-question MCQ quiz. Score below 70%?
          The plan self-corrects. Score above? You advance.
        </p>
      </article>
    </div>
  </section>

  <!-- ── Footer ─────────────────────────────────────────────────────────── -->
  <footer class="footer">
    <p>
      Built with ❤️ for
      <strong>AICTE AI Automation &amp; Intelligent Solutions — IBM SkillsBuild 2026</strong>
    </p>
    <p class="footer-stack">
      SvelteKit · FastAPI · Modal · LangGraph · Supabase · DeepSeek V4 Flash
    </p>
  </footer>
</main>

<style>
  /* ── Layout ── */
  .root {
    min-height: 100vh;
    position:   relative;
    overflow-x: hidden;
  }

  /* ── Ambient background orbs ── */
  .bg-mesh {
    position:       fixed;
    inset:          0;
    pointer-events: none;
    z-index:        0;
  }
  .orb {
    position:      absolute;
    border-radius: 50%;
    filter:        blur(90px);
  }
  .orb-1 {
    width:      700px; height: 700px;
    background: radial-gradient(circle, rgba(108,71,255,0.22) 0%, transparent 70%);
    top: -260px; left: -200px;
    animation: pulseRing 9s ease-in-out infinite;
  }
  .orb-2 {
    width:      500px; height: 500px;
    background: radial-gradient(circle, rgba(0,212,170,0.14) 0%, transparent 70%);
    bottom: 150px; right: -150px;
    animation: pulseRing 11s ease-in-out infinite 2s;
  }
  .orb-3 {
    width:      350px; height: 350px;
    background: radial-gradient(circle, rgba(108,71,255,0.10) 0%, transparent 70%);
    top: 55%; left: 40%;
    animation: pulseRing 13s ease-in-out infinite 4s;
  }
  @keyframes pulseRing {
    0%,100% { transform: scale(1);    opacity: 1; }
    50%     { transform: scale(1.08); opacity: 0.4; }
  }

  /* ── Nav ── */
  .nav {
    position:        relative;
    z-index:         10;
    display:         flex;
    align-items:     center;
    justify-content: space-between;
    padding:         1.5rem 2.5rem;
    max-width:       1200px;
    margin:          0 auto;
  }
  .nav-logo {
    display:     flex;
    align-items: center;
    gap:         0.45rem;
    font-size:   1.2rem;
    font-weight: 700;
    color:       var(--color-text);
  }
  .nav-link {
    color:           var(--color-muted);
    text-decoration: none;
    font-size:       0.9rem;
    transition:      color 0.2s;
  }
  .nav-link:hover { color: var(--color-text); }

  /* ── Hero ── */
  .hero {
    position:        relative;
    z-index:         5;
    display:         flex;
    align-items:     center;
    justify-content: center;
    min-height:      calc(100vh - 76px);
    padding:         5rem 2rem 7rem;
  }
  .hero-content {
    text-align:      center;
    max-width:       780px;
    display:         flex;
    flex-direction:  column;
    align-items:     center;
    gap:             2rem;
  }
  .headline {
    font-size:      clamp(2.6rem, 6vw, 4.8rem);
    font-weight:    800;
    line-height:    1.08;
    letter-spacing: -0.025em;
    margin:         0;
  }
  .subhead {
    font-size:   1.1rem;
    color:       var(--color-muted);
    line-height: 1.75;
    max-width:   600px;
    margin:      0;
  }
  .stats-row {
    display:         flex;
    align-items:     center;
    gap:             1.25rem;
    flex-wrap:       wrap;
    justify-content: center;
  }
  .stat {
    display:     flex;
    align-items: center;
    gap:         0.4rem;
    font-size:   0.9rem;
    color:       var(--color-muted);
  }
  .stat-sep {
    width:      1px;
    height:     16px;
    background: var(--color-border);
  }
  .cta-row {
    display:         flex;
    gap:             1rem;
    flex-wrap:       wrap;
    justify-content: center;
  }
  .btn-hero {
    padding:       0.9rem 2.25rem;
    font-size:     1.05rem;
    border-radius: 14px;
  }

  /* ── How it works ── */
  .how {
    position:   relative;
    z-index:    5;
    padding:    6rem 2rem;
    max-width:  1100px;
    margin:     0 auto;
  }
  .how h2 {
    text-align:   center;
    font-size:    2.1rem;
    font-weight:  700;
    margin-bottom: 3rem;
  }
  .steps-grid {
    display:               grid;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap:                   1.25rem;
  }
  .step-card { display: flex; flex-direction: column; gap: 0.7rem; }
  .step-num {
    font-size:       0.72rem;
    font-weight:     700;
    letter-spacing:  0.12em;
    color:           var(--color-accent);
    text-transform:  uppercase;
  }
  .step-icon { font-size: 2rem; }
  .step-card h3 { font-size: 1.1rem; font-weight: 600; margin: 0; }
  .step-card p  { font-size: 0.9rem; color: var(--color-muted); line-height: 1.65; margin: 0; }

  /* ── Footer ── */
  .footer {
    position:    relative;
    z-index:     5;
    text-align:  center;
    padding:     3rem 2rem;
    border-top:  1px solid var(--color-border);
    color:       var(--color-muted);
    font-size:   0.875rem;
  }
  .footer p { margin: 0.3rem 0; }
  .footer-stack { font-size: 0.78rem; opacity: 0.55; }

  /* ── Responsive ── */
  @media (max-width: 600px) {
    .nav    { padding: 1.2rem 1.25rem; }
    .hero   { padding: 3rem 1.25rem 5rem; }
    .stat-sep { display: none; }
    .how    { padding: 4rem 1.25rem; }
  }
</style>
