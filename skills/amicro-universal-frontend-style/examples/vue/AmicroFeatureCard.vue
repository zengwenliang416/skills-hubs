<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{ title: string; description: string }>();
const emit = defineEmits<{ apply: [] }>();
const status = ref<"idle" | "done">("idle");

function apply() {
  emit("apply");
  status.value = "done";
  window.setTimeout(() => (status.value = "idle"), 1400);
}
</script>

<template>
  <!-- Self-scoped for copy/paste use; remove `amicro` only inside an existing Amicro scope. -->
  <article class="amicro amicro-card amicro-hover-lift" data-amicro-root data-amicro-theme="auto" data-interactive="true">
    <div class="amicro-card__stage" style="padding: 1.25rem">
      <div class="amicro-stack">
        <span class="amicro-chip">Vue · CSS first</span>
        <h3 class="amicro-heading">{{ props.title }}</h3>
        <p class="amicro-copy">{{ props.description }}</p>
      </div>
    </div>
    <footer class="amicro-card__footer">
      <span class="amicro-card__meta" aria-live="polite">{{ status === "done" ? "Change saved" : "Scoped variables" }}</span>
      <button class="amicro-button amicro-pressable" data-variant="primary" type="button" @click="apply">
        {{ status === "done" ? "Applied" : "Apply style" }}
      </button>
    </footer>
  </article>
</template>
