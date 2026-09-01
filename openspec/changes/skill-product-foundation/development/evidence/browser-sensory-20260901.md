# Browser Inspection Evidence: 2026-09-01

## Runtime

- Frontend: `http://localhost:5173/`
- Backend: `http://127.0.0.1:8080/`
- Desktop viewport: `1440x1000`
- Mobile viewport: `320x812`
- System media state: light color scheme, reduced motion disabled.

## Desktop

- The page rendered two Skills, real visitor metrics, per-Skill engagement, and npm availability.
- npm summary rendered `1/2 个包有数据`; the unavailable package rendered `暂无数据` and an em dash rather than a confirmed zero.
- Expanded-field search for `GPT Image` returned only Image API Workbench.
- Image API Workbench detail rendered description, tags, highlights, use cases, two install methods, quick start, metadata, documentation, and source links.
- Initial dialog focus was `关闭详情`; `Escape` closed the dialog and returned focus to the originating Skill button.
- Copying the npm command produced the accessible `已复制` state without blocking the action.
- Theme cycling produced `light`, `dark`, and `auto` root states with matching `color-scheme`.
- Browser console warning/error query returned an empty list.

## Mobile

- Before repair, the 320px viewport exposed page-level horizontal scrolling because `body` required 320px in addition to the vertical scrollbar and flex title content could not shrink.
- After repair, the page and catalog rendered without a horizontal scrollbar.
- The catalog stacked both Skill cards at 320px without clipping.
- The open detail measured 269px wide inside a 305px document client width, with no horizontal overflow.
- The detail used internal vertical scrolling (`clientHeight=794`, `scrollHeight=2137`) and kept initial focus on `关闭详情`.
- Documentation and source actions remained reachable at the end of the mobile dialog.

## End-To-End Aggregate Observation

- Repeated reloads from the same local IP increased page views while total visitors remained `1`.
- Image API Workbench aggregate values reached views `6`, install copies `3`, documentation clicks `2`, repository clicks `2`, and unique visitors `1`.
- API responses exposed aggregate values only and did not expose raw visitor IPs.

## Boundary

- The connected browser did not expose reduced-motion media emulation. Reduced-motion behavior is guarded in runtime code and passed Amicro strict static checks, but the live sensory case remains assigned to Verification.
