<script lang="ts">
  export let title: string;
  export let description: string;
  export let onApply: () => void = () => {};

  let done = false;
  function apply() {
    onApply();
    done = true;
    window.setTimeout(() => (done = false), 1400);
  }
</script>

<!-- Self-scoped for copy/paste use; remove `amicro` only inside an existing Amicro scope. -->
<article class="amicro amicro-card amicro-hover-lift" data-amicro-root data-amicro-theme="auto" data-interactive="true">
  <div class="amicro-card__stage" style="padding: 1.25rem">
    <div class="amicro-stack">
      <span class="amicro-chip">Svelte · CSS first</span>
      <h3 class="amicro-heading">{title}</h3>
      <p class="amicro-copy">{description}</p>
    </div>
  </div>
  <footer class="amicro-card__footer">
    <span class="amicro-card__meta" aria-live="polite">{done ? "Change saved" : "Framework native"}</span>
    <button class="amicro-button amicro-pressable" data-variant="primary" type="button" on:click={apply}>
      {done ? "Applied" : "Apply style"}
    </button>
  </footer>
</article>
