---
version: "1.0"
name: Skills Hub Amicro Design System
description: Amicro-scoped design rules for the Skills Hub React application.
colors:
  text: "var(--amicro-text)"
  text-muted: "var(--amicro-text-muted)"
  surface: "var(--amicro-surface)"
  stage: "var(--amicro-stage)"
  border: "var(--amicro-border)"
  focus: "var(--amicro-focus)"
  success: "var(--amicro-success)"
  danger: "var(--amicro-danger)"
typography:
  display:
    fontFamily: "var(--amicro-font-display)"
    fontSize: "var(--amicro-font-size-display)"
    fontWeight: 600
    lineHeight: "var(--amicro-line-tight)"
  heading:
    fontFamily: "var(--amicro-font-body)"
    fontSize: "var(--amicro-font-size-xl)"
    fontWeight: 600
    lineHeight: "var(--amicro-line-compact)"
  body:
    fontFamily: "var(--amicro-font-body)"
    fontSize: "var(--amicro-font-size-md)"
    fontWeight: 400
    lineHeight: "var(--amicro-line-body)"
  mono:
    fontFamily: "var(--amicro-font-mono)"
    fontSize: "var(--amicro-font-size-sm)"
    fontWeight: 400
    lineHeight: "var(--amicro-line-body)"
spacing:
  xs: "var(--amicro-space-1)"
  sm: "var(--amicro-space-2)"
  md: "var(--amicro-space-4)"
  lg: "var(--amicro-space-6)"
  xl: "var(--amicro-space-8)"
rounded:
  control: "var(--amicro-radius-control)"
  stage: "var(--amicro-radius-stage)"
  card: "var(--amicro-radius-card)"
components:
  button:
    source: "web/src/components/Button.tsx"
    minHeight: "40px"
    focus: "var(--amicro-focus)"
  card:
    source: "web/src/components/StageCard.tsx"
    surface: "var(--amicro-surface)"
    radius: "var(--amicro-radius-card)"
  dialog:
    source: "web/src/features/catalog/SkillDetailDialog.tsx"
    surface: "var(--amicro-surface)"
    radius: "var(--amicro-radius-card)"
---

# Skills Hub Amicro Design System

## Overview

The web application uses the scoped Amicro token layer in
`web/src/styles/amicro-tokens.css`. Feature styles must consume those semantic
tokens through CSS Modules and preserve the existing editorial direction,
accessibility behavior, and responsive layout.

## Colors

Use semantic Amicro variables for text, muted copy, page and stage surfaces,
borders, focus, success, and danger states. State must pair color with text or an
icon. Feature code must not introduce a parallel palette.

## Typography

Display headings use the existing expressive display role; body copy uses the
Amicro body role and commands or paths use the mono role. New Skill detail
content must preserve a readable hierarchy between description, section
headings, lists, metadata, and commands.

## Layout

Sections share the existing centered page width and responsive rhythm. Skill
details may use a wider dialog than the metadata-only version, but must fit a
320px viewport, use an internal scrolling region when necessary, and avoid
horizontal page overflow. Dense content collapses to one column on narrow screens.

## Elevation & Depth

Use borders and distinct surface/stage tokens before adding shadows. Dialogs use
the existing overlay and float shadow. Interactive content inside a dialog must
retain a visible focus ring and clear hover-independent affordance.

## Motion

Motion remains purposeful and optional. Non-essential transitions must be
inside `prefers-reduced-motion: no-preference`; reduced-motion users receive
immediate state changes. Event reporting must never delay navigation, dialog
opening, copying, or closing.

## Shapes

Controls use the control radius, content groups use the stage radius, and major
cards/dialogs use the card radius. Tags remain pill-like through the existing
Chip component.

## Components

Reuse Button, IconButton, Chip, StageCard, FadeUp, and the native dialog
discipline already present. The expanded Skill detail remains a domain
component; repeated install-method or engagement rendering belongs within the
owning catalog or metrics feature.

## Voice & Content

User-facing copy is concise Simplified Chinese. Technical names, commands,
paths, package names, and API identifiers remain unchanged. Unavailable npm
data is described as unavailable or partial, never silently converted into a
confirmed zero.

## Theme & Internationalization

- Theme capability: `system`, with explicit `light`, `dark`, and `auto` modes.
- Theme toggle policy: the existing header control cycles all three modes.
- Prototype coverage: changed surfaces cover light, dark, and auto modes.
- Internationalization capability: none; there is no locale runtime or routing.
- Supported locales: `zh-CN`.
- Default locale: `zh-CN`.
- Locale switcher policy: omit until an i18n runtime and translations exist.

## Do's and Don'ts

- Do use `--amicro-*` tokens and current components.
- Do preserve keyboard, touch, reduced-motion, and focus behavior.
- Do show content and analytics empty/error states explicitly.
- Don't add a new component library or CSS framework.
- Don't hide tracking failures behind blocking UI.
- Don't invent release dates, registry availability, or usage claims.
