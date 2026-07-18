<script>
  /** @type {{ index: number, text: string }} */
  export let option;
  export let selected = false;
  /** @type {(index: number) => void} */
  export let onSelect;
</script>

<button
  id="quiz-option-{option.index}"
  class="quiz-option"
  class:selected
  on:click={() => onSelect(option.index)}
  aria-pressed={selected}
  type="button"
>
  <span class="option-letter" aria-hidden="true">
    {String.fromCharCode(65 + option.index)}
  </span>
  <span class="option-text">{option.text}</span>

  {#if selected}
    <span class="check-icon" aria-hidden="true">✓</span>
  {/if}
</button>

<style>
  .quiz-option {
    width:           100%;
    display:         flex;
    align-items:     center;
    gap:             1rem;
    padding:         1rem 1.25rem;
    background:      var(--color-surface);
    border:          1px solid var(--color-border);
    border-radius:   var(--radius);
    color:           var(--color-text);
    font-size:       0.95rem;
    font-family:     inherit;
    text-align:      left;
    cursor:          pointer;
    transition:      border-color 0.18s, background 0.18s, transform 0.15s;
  }

  .quiz-option:hover:not(.selected) {
    border-color: var(--color-border-hover);
    background:   var(--color-surface-2);
    transform:    translateX(3px);
  }

  .quiz-option.selected {
    border-color: var(--color-accent);
    background:   rgba(108, 71, 255, 0.1);
    box-shadow:   0 0 0 1px var(--color-accent);
  }

  .option-letter {
    display:         inline-flex;
    align-items:     center;
    justify-content: center;
    width:           32px;
    height:          32px;
    border-radius:   50%;
    background:      rgba(255, 255, 255, 0.07);
    font-size:       0.82rem;
    font-weight:     700;
    flex-shrink:     0;
    transition:      background 0.18s, color 0.18s;
  }

  .selected .option-letter {
    background: var(--color-accent);
    color:      white;
  }

  .option-text {
    flex:        1;
    line-height: 1.5;
  }

  .check-icon {
    font-size:  0.9rem;
    color:      var(--color-accent);
    font-weight: 700;
    flex-shrink: 0;
  }
</style>
