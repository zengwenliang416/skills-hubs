export type SkillEventType =
  'skill_view' | 'install_copy' | 'documentation_click' | 'repository_click'

/** Best-effort first-party analytics; primary UI actions never wait for it. */
export function reportSkillEvent(skillName: string, eventType: SkillEventType): void {
  void fetch('/api/events', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      skill_name: skillName,
      event_type: eventType,
    }),
    keepalive: true,
  }).catch(() => undefined)
}
