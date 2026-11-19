# Intenda Product Specification v1.0

**Product:** Intenda 意达 --- Agent-native Email\
**Document status:** Engineering-ready product and implementation
specification\
**Version:** 1.0\
**Date:** 19 November 2026\
**Primary experience:** Desktop web application, responsive down to
tablet\
**Demo deployment target:** One deployable web service on Render Free,
with a publicly accessible test URL\
**AI provider:** Groq free tier through an OpenAI-compatible API, model
`openai/gpt-oss-20b`\
**Design system:** V4 black / white / neutral-grey foundation, one blue
accent `#2563EB`, Day and Night modes

------------------------------------------------------------------------

# Section 1 --- Product definition, goals and system principles

## 1.1 Product definition

Intenda is an Agent-native email workspace. It preserves the familiar
capabilities of email while changing the primary interaction from
manually operating every message to expressing a desired outcome and
delegating the work to an Agent.

The user describes the result they want. Intenda's Agent reads the
relevant email context, proposes a plan, performs permitted work,
reports progress, and returns reviewable outputs. The user remains in
control: manual email operations remain available, and external or
consequential actions are governed by explicit authorization and human
confirmation.

**Product promise:** Tell Intenda what outcome you want; it understands
the email context, moves the work forward, and brings back a result you
can inspect and control.

**Mission:** Turn email intent into completed, reviewable work without
taking control away from the user.

**Brand:** Intenda 意达\
**Positioning:** An email workspace where people delegate outcomes to an
Agent while retaining visibility, authority and a conventional inbox.\
**Brand attributes:** Clear, dependable, deliberate, capable, calm.\
**Brand line:** From Intent to Done.

## 1.2 The problem

Traditional email clients are organized around messages and manual
operations. Users repeatedly search for context, identify the next
action, compose responses, follow up, create reminders, coordinate
meetings, and track whether work has actually been completed.

Generic AI email features often stop at summarization or drafting. They
do not provide a coherent, inspectable task lifecycle with explicit
authorization, progress, decisions, review, and recovery.

Intenda addresses this gap by treating email as a work context and the
Agent as a supervised execution layer.

## 1.3 Target users

1.  **Knowledge workers and operators:** People managing a high volume
    of correspondence, follow-ups, scheduling, approvals and
    coordination.
2.  **Founders and small teams:** People who need to move customer,
    partner, vendor and investor conversations forward without hiring a
    dedicated assistant.
3.  **Consultants and client-facing professionals:** People who need to
    preserve context across threads and produce careful, consistent
    communication.
4.  **Technical evaluators and interviewers:** Reviewers who need to
    test the product through a public demo without connecting a personal
    mailbox.

The first release is optimized for an individual user. Shared team
inboxes, organization-wide policy administration and multi-user task
assignment are outside the v1.0 release scope.

## 1.4 Core user jobs

-   Understand what needs attention today.
-   Find, read, search and manage email.
-   Ask the Agent to summarize a thread or explain what is being
    requested.
-   Delegate a concrete outcome in natural language.
-   Inspect the Agent's proposed plan and choose an authorization level.
-   Watch task progress and intervene when needed.
-   Review, edit, approve or reject generated email drafts.
-   Send, reply, forward, archive or delete messages manually.
-   Create and manage reminders and recurring automations.
-   See which data is simulated and which activity is connected to a
    real provider.

## 1.5 Product principles

1.  **Intent first, not automation at any cost.** The Agent should
    understand the requested outcome and show a plan before acting.
2.  **Human authority is explicit.** Authorization is selected by the
    user, visible during execution, and enforced by the backend.
3.  **No invisible side effects.** Sending, deleting, changing account
    settings or other consequential actions require explicit permission
    and are logged.
4.  **Manual operation remains first-class.** Every core email action
    can be completed without the Agent.
5.  **Progress is inspectable.** Tasks expose steps, timestamps, status,
    decisions, errors and produced drafts.
6.  **Truthful demo.** Seeded mailbox content and simulated provider
    activity are visibly labelled. The product must never imply that a
    simulated message was delivered to a real recipient.
7.  **Graceful degradation.** If the free AI model is unavailable, the
    user can continue manually and no action is silently taken.
8.  **Privacy by default.** Only the minimum email context required for
    the requested task is sent to the model. Provider credentials remain
    server-side.

## 1.6 V1.0 scope

### Included

-   Account registration, login and session management.
-   First-run onboarding and email account binding.
-   A clearly labelled Demo Mailbox for reviewers.
-   Day and Night themes.
-   Eight complete application pages: Today Briefing, Delegate Work,
    Task Progress, Inbox, Review Queue, Automations, Archive and
    Settings.
-   Email list, reading, search, compose, reply, forward, archive,
    delete and Agent handoff.
-   Agent chat using Groq's free tier and `openai/gpt-oss-20b`.
-   Plan generation, authorization selection, task execution, live
    progress, pause, resume, takeover and termination.
-   Draft delivery to Review Queue.
-   Basic to-do creation and reminder/automation management.
-   Audit log for meaningful user and Agent actions.
-   Seeded demo data and simulated sync.
-   REST API and WebSocket progress events.

### Excluded from V1.0

-   Paid AI model providers or paid AI fallback.
-   Paid email sending infrastructure or paid automation services.
-   Shared team inboxes, organization roles and multi-tenant enterprise
    administration.
-   Autonomous bulk sending, autonomous deletion, or autonomous
    account/security changes.
-   Financial transactions, purchases, subscriptions or payments.
-   Calendar write access unless separately introduced in a later,
    explicitly authorized integration.
-   Training a model on user mailbox content.
-   Claiming that demo sync or demo sends have reached an external mail
    provider.

## 1.7 V4 visual system --- locked decisions

The V4 visual direction is black-and-white-led, restrained and
professional. The interface uses neutral surfaces and typography as its
foundation. **The only brand/action blue is `#2563EB`. There is no
purple anywhere in the product.** The same blue is used for primary
buttons, selected navigation, selection indicators, notification dots
and avatar backgrounds. Do not add a second blue for hover, focus or
status. Hover and focus may change opacity, border thickness or
elevation while retaining the same blue value.

Small-area macaron/khaki tones may be used for low-priority semantic
status backgrounds and decorative details. They must not compete with
the neutral foundation or the single blue accent.

### 1.7.1 Day mode tokens

  -----------------------------------------------------------------------------
  Token                                               Hex Use
  -------------------------- ---------------------------- ---------------------
  `day.background`                              `#F5F6F8` Application canvas

  `day.sidebar`                                 `#ECEFF2` Left navigation

  `day.topbar`                                  `#FFFFFF` Top bar

  `day.surface.1`                               `#FFFFFF` Main cards and panels

  `day.surface.2`                               `#F7F8FA` Nested panels and
                                                          list regions

  `day.surface.elevated`                        `#FFFFFF` Menus, dialogs and
                                                          popovers

  `day.surface.hover`                           `#EDF1F5` Hovered neutral
                                                          surface

  `day.border`                                  `#D8DDE3` Card and control
                                                          outlines

  `day.divider`                                 `#E7EAEE` Hairline separators

  `day.text.primary`                            `#161B22` Headings and main
                                                          content

  `day.text.secondary`                          `#4F5965` Supporting text

  `day.text.tertiary`                           `#7A8490` Metadata and
                                                          placeholders

  `day.accent`                                  `#2563EB` The single blue
                                                          accent

  `day.accent.hover`                            `#2563EB` Same blue; use
                                                          opacity/elevation for
                                                          hover

  `day.accent.surface`                          `#EAF0FF` Pale tint derived
                                                          from the same accent

  `day.success.foreground`                      `#657A6B` Muted grey-green
                                                          status text

  `day.success.background`                      `#E9EFEA` Muted success
                                                          background

  `day.warning.foreground`                      `#8A7350` Muted khaki status
                                                          text

  `day.warning.background`                      `#F3EDE2` Muted warning
                                                          background

  `day.danger.foreground`                       `#94696B` Muted rose-brown
                                                          status text

  `day.danger.background`                       `#F3E9E9` Muted danger
                                                          background

  `day.info.foreground`                         `#687782` Neutral slate status
                                                          text

  `day.info.background`                         `#E9EEF1` Neutral information
                                                          background

  `day.avatar.background`                       `#2563EB` Initial/avatar
                                                          background

  `day.avatar.foreground`                       `#FFFFFF` Avatar initials
  -----------------------------------------------------------------------------

### 1.7.2 Night mode tokens

  -------------------------------------------------------------------------------
  Token                                                 Hex Use
  ---------------------------- ---------------------------- ---------------------
  `night.background`                              `#0B0D10` Application canvas

  `night.sidebar`                                 `#101317` Left navigation

  `night.topbar`                                  `#0F1216` Top bar

  `night.surface.1`                               `#151A20` Main cards and panels

  `night.surface.2`                               `#1B2128` Nested panels and
                                                            list regions

  `night.surface.elevated`                        `#222A33` Menus, dialogs and
                                                            popovers

  `night.surface.hover`                           `#252D36` Hovered neutral
                                                            surface

  `night.border`                                  `#303943` Card and control
                                                            outlines

  `night.divider`                                 `#252C34` Hairline separators

  `night.text.primary`                            `#F4F6F8` Headings and main
                                                            content

  `night.text.secondary`                          `#B6BEC7` Supporting text

  `night.text.tertiary`                           `#7F8994` Metadata and
                                                            placeholders

  `night.accent`                                  `#2563EB` The single blue
                                                            accent

  `night.accent.hover`                            `#2563EB` Same blue; use
                                                            opacity/elevation for
                                                            hover

  `night.accent.surface`                          `#17264A` Dark tint derived
                                                            from the same accent

  `night.success.foreground`                      `#A9B9AE` Muted grey-green
                                                            status text

  `night.success.background`                      `#26312B` Muted success
                                                            background

  `night.warning.foreground`                      `#C3B18E` Muted khaki status
                                                            text

  `night.warning.background`                      `#383124` Muted warning
                                                            background

  `night.danger.foreground`                       `#C49A9C` Muted rose-brown
                                                            status text

  `night.danger.background`                       `#38282A` Muted danger
                                                            background

  `night.info.foreground`                         `#A9B5BD` Neutral slate status
                                                            text

  `night.info.background`                         `#293138` Neutral information
                                                            background

  `night.avatar.background`                       `#2563EB` Initial/avatar
                                                            background

  `night.avatar.foreground`                       `#FFFFFF` Avatar initials
  -------------------------------------------------------------------------------

The accent surface tokens are neutralized tints for selection
backgrounds, not additional action colors. All actionable blue elements
use `#2563EB`. Do not use purple, violet, indigo, cyan or another blue
as a second accent.

### 1.7.3 Typography

-   Primary Latin font: **Inter**.
-   Chinese font: **Noto Sans SC**.
-   CSS stack:
    `Inter, "Noto Sans SC", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`.
-   Default body size: 14px / 20px line height.
-   Secondary metadata: 12px / 16px.
-   Labels and controls: 13px / 18px.
-   Section headings: 18px / 26px, weight 600.
-   Page title: 24px / 32px, weight 650.
-   Hero metric: 28--32px / 36--40px, weight 650.
-   Dialog title: 18px / 26px, weight 600.
-   Use tabular numerals for counts, timestamps and progress
    percentages.

### 1.7.4 Layout and component rules

-   Desktop reference viewport: 1440 × 900.
-   Sidebar width: 248px, fixed on desktop.
-   Top bar height: 64px.
-   Main content padding: 28--32px.
-   Standard card radius: 12px.
-   Compact control radius: 8px.
-   Pill radius: 999px for status chips only.
-   Standard button height: 40px; compact button height: 32px.
-   Standard spacing scale: 4, 8, 12, 16, 20, 24, 32, 40, 48px.
-   Borders are thin and neutral. Avoid glassmorphism, neon, purple
    gradients, excessive shadows and decorative AI motifs.
-   Primary buttons use `#2563EB` with white text. Secondary buttons use
    neutral surfaces and borders. Destructive actions use neutral
    outline styling plus explicit confirmation, not a bright red filled
    button.
-   Status colors are muted and limited to small labels or status
    backgrounds. They are never used as large functional button fills.

## 1.8 Product success criteria

V1.0 is successful when a new reviewer can open the public test link,
register or enter the demo, understand that the mailbox is simulated,
ask the Agent to perform a realistic email task, inspect the plan,
choose an authorization level, observe progress, review the resulting
draft, edit it and approve the simulated send without dead ends.

Primary product metrics:

-   Onboarding completion rate.
-   Time from opening the app to first successful Agent conversation.
-   Delegation plan acceptance rate.
-   Percentage of tasks reaching a reviewable result.
-   Review approval/edit/reject distribution.
-   Email search and manual-operation success rate.
-   Number of failed or ambiguous external side effects (target: zero).
-   Percentage of demo actions correctly labelled as simulated.
-   Recovery success after model timeout, provider error or WebSocket
    disconnect.

------------------------------------------------------------------------

# Section 2 --- Information architecture, navigation and theme

## 2.1 Application shell

The authenticated application uses a consistent desktop shell:

-   **Left sidebar:** 248px wide, full viewport height, fixed
    navigation.
-   **Top bar:** 64px high, aligned to the content area. It contains
    page context, global search entry, quick compose, sync state and
    account menu. It does not contain the Day/Night toggle.
-   **Content region:** fills the remaining viewport and scrolls
    independently where appropriate.
-   **Optional contextual rail:** used on Today Briefing, Task Progress
    and Review Queue when it materially improves the workflow. It must
    not shrink the main work area below a usable width.

At 1440px width, the content region begins at x=248. The application
must not use a marketing-site layout after login; it is a working email
terminal.

## 2.2 Sidebar structure

The sidebar contains the Intenda logo at the top, followed by the eight
routes in this order:

1.  Today Briefing
2.  Delegate Work
3.  Task Progress
4.  Inbox
5.  Review Queue
6.  Automations
7.  Archive
8.  Settings

The active route has a neutral selected background and a narrow
`#2563EB` indicator. Unread and pending counts appear as compact badges.
The Settings route remains a normal navigable page.

At the bottom-left of the sidebar, place the appearance control. It
replaces the old standalone Settings gear location and is visually
separate from the route list.

## 2.3 Day/Night appearance toggle --- mandatory placement and behaviour

### Placement and form

-   The toggle is fixed at the bottom-left of the sidebar, above the
    user/account footer if one exists.
-   It is absent from the top bar. No duplicate appearance control may
    appear in the top bar.
-   The control is a full-width sidebar row with:
    -   A sun/moon icon that reflects the current mode.
    -   Text label **Appearance**.
    -   A compact current-state value: **Day** or **Night**.
    -   A chevron indicating that the row opens a small menu.
-   In Day mode, use a sun icon and show `Day`.
-   In Night mode, use a moon icon and show `Night`.
-   The row uses neutral surfaces. The blue accent is not used as a
    large background.

### Interaction

Selecting the row opens a compact menu with two radio options: Day and
Night. Selecting either option immediately changes the theme without
page reload. The selected option is marked with a check and
`aria-checked=true`. Selecting the current mode closes the menu without
additional work.

The application must not automatically switch modes while the user is
working. On first visit only, if the account has no saved preference,
initialize from the operating-system preference. Once the user selects a
mode, that explicit choice takes precedence.

### Persistence

-   Persist the preference to the user settings record through
    `PATCH /api/v1/settings`.
-   Cache the preference locally for immediate paint and offline
    continuity.
-   On login, the server preference is authoritative; if no server
    preference exists, use the local preference, then system preference,
    then Day as final fallback.
-   A theme change is applied to all routes and dialogs immediately.
-   If the settings request fails, retain the local selection, show a
    non-blocking message, and retry synchronization on the next
    successful connection.

### Keyboard and accessibility

-   Implement as a native button with an accessible name such as
    `Appearance, current mode Night`.
-   Enter or Space opens the menu.
-   Arrow keys move between Day and Night options.
-   Enter or Space selects the focused option.
-   Escape closes the menu and returns focus to the trigger.
-   Tab moves through the menu in normal document order.
-   Use visible focus rings in the current theme. The focus ring uses
    `#2563EB`.
-   Expose `aria-haspopup="menu"` or an equivalent accessible menu
    pattern, `aria-expanded`, and radio state.
-   Do not rely on color alone to communicate the current mode.
-   Respect reduced-motion preferences; theme transition may use a short
    100--150ms color transition, but must not animate layout.

## 2.4 Routes

  ----------------------------------------------------------------------------------
  Page                    Route                              Purpose
  ----------------------- ---------------------------------- -----------------------
  Today Briefing          `/app/briefing`                    Daily overview and
                                                             decisions

  Delegate Work           `/app/delegate`                    Express intent and
                                                             create a task

  Task Progress           `/app/tasks` and                   Monitor and control
                          `/app/tasks/:taskId`               execution

  Inbox                   `/app/inbox` and                   Manual email work
                          `/app/inbox/:threadId`             

  Review Queue            `/app/review` and                  Inspect and approve
                          `/app/review/:reviewId`            Agent outputs

  Automations             `/app/automations` and             Manage recurring rules
                          `/app/automations/:automationId`   

  Archive                 `/app/archive`                     Find and restore
                                                             archived mail

  Settings                `/app/settings`                    Account, connected
                                                             mailboxes, Agent and
                                                             preferences
  ----------------------------------------------------------------------------------

Every sidebar entry must resolve to a complete working page. No
placeholder route, inert button or decorative-only action is permitted.

## 2.5 Shared interaction and state requirements

Every page must provide:

-   A loading state with skeletons matching the final layout.
-   An empty state with a useful explanation and a next action.
-   An error state with a human-readable message, retry action and
    preserved user input where safe.
-   Success and failure feedback for mutations.
-   Disabled and pending states during network operations.
-   Confirmation for destructive or externally visible actions.
-   Keyboard focus management and screen-reader labels.
-   Clear demo/live labels wherever data or operations could be mistaken
    for real activity.

### 2.5.1 Today Briefing

**Purpose:** Give the user a concise, actionable view of the day.

**Layout** - Page title `今日简报` / `Today Briefing`, date and
last-updated time. - Summary metric row: New Mail, Needs Decision, In
Progress, Delivered. - Main column: `需要你决策` / Needs Your
Decision. - Secondary column: `Agent 正在推进` / Agent in Progress. -
Lower section: Recent activity and priority messages.

**Core components** - Metric cards with counts and links to filtered
views. - Decision cards showing task ID, subject, recipient, Agent
recommendation, impact, due date and Approve / Modify / Reject
actions. - Task progress rows with status, percent, last event and Open
Task action. - Recent email list with sender, subject, snippet and
unread state. - Demo/live provenance badge near the page title or data
summary.

**Data source** - `GET /api/v1/briefing` - Aggregates email counts,
pending review items, task states, recent activity and unread counts.

**Empty state** - If no mailbox is connected: show
`Connect an email account or open the Demo Mailbox` with both actions. -
If no decisions are pending: show
`You're up to date. There are no decisions waiting for you.` - If no
tasks are running: show a Delegate Work call to action.

**Loading state** - Skeleton metric cards, decision cards and progress
rows. Do not show misleading zero counts while loading.

**Error state** - Preserve the page shell and display a retry banner:
`We couldn't load your briefing. Your mailbox and tasks have not been changed.`
Retry calls the briefing endpoint again.

**Primary actions and feedback** - Open decision → Review Queue
detail. - Approve/modify/reject → decision API; show pending state and
then a success toast or actionable error. - Open task → Task Progress
detail. - Open message → Inbox thread. - Start delegation → Delegate
Work. - Refresh → re-fetch aggregate data. - Every metric card is
clickable and navigates to its corresponding filtered page.

### 2.5.2 Delegate Work

**Purpose:** Let the user describe a desired outcome and convert it into
a safe, inspectable plan.

**Layout** - Page title and short explanatory text. - Large
natural-language intent composer. - Context selector for relevant
mailbox, thread, contacts and attachments. - Suggested intent chips. -
Agent response/plan area. - Authorization selector. - Primary
`Start execution` button.

**Core components** - Multiline intent input with character count and
example prompts. - Context chips showing selected threads/messages and
removable selections. - Agent plan list with numbered steps, expected
outputs and risk indicators. - Authorization options: 1. **Confirm Every
Step** 2. **Confirm at Key Milestones** 3. **Fully Automatic but Confirm
Before Sending** - Plan summary with recipients, affected threads,
external side effects and estimated actions. - Start button remains
disabled until intent is valid, plan exists and authorization is
selected.

**Data source** - `POST /api/v1/agent/conversations` -
`POST /api/v1/agent/messages` for intent analysis and plan generation. -
`POST /api/v1/tasks` after the user confirms the plan and authorization.

**Empty state** - Explain what the Agent can do and provide safe
examples: summarize a thread, draft a follow-up, prepare a meeting
response. - No context selected is valid; the Agent may ask a clarifying
question.

**Loading state** - Show `Understanding your request…`, then stream the
Agent response. Keep the composer visible and prevent duplicate
submission.

**Error state** - Preserve the user's text and selected context. If the
model is unavailable, show the exact fallback wording defined in Section
5. Do not create a task from a failed plan-generation request.

**Primary actions and feedback** - Send intent → stream plan/clarifying
question. - Add/remove context → update context list. - Select
authorization → visibly summarize the exact permission boundary. - Start
execution → create task and navigate to Task Progress. - Save as draft
intent → persist the conversation without creating a task. - Clear → ask
for confirmation if unsaved text exists. - No action may execute merely
because the user typed an intent; the explicit Start execution action is
required.

### 2.5.3 Task Progress

**Purpose:** Make Agent execution visible, controllable and recoverable.

**Layout** - Task list or task detail view. - Detail header with task
ID, goal, owner, authorization level and progress. - Main vertical
timeline of steps and events. - Context panel showing affected threads
and selected sources. - Decision panel for any current approval gate. -
Output panel containing drafts, to-dos and files/links produced.

**Core components** - Task status chip and progress bar. - Step timeline
with queued, running, waiting, completed, failed and skipped states. -
Event log with timestamp and actor (`You`, `Agent`, `System`). - Pause,
Resume, Take Over and Terminate controls as appropriate to state. -
Decision cards for milestones. - Result cards linking to Review Queue
drafts. - Clear indicator when an action is simulated.

**Data source** - `GET /api/v1/tasks` - `GET /api/v1/tasks/:taskId` -
`GET /api/v1/tasks/:taskId/events` - WebSocket `/api/v1/ws` for
real-time updates.

**Empty state** -
`No tasks yet. Delegate an outcome to see the Agent's work here.` with
Start a delegation action.

**Loading state** - Skeleton header, timeline and output cards.
Reconnect to WebSocket after initial REST load.

**Error state** - If task details fail, retain task ID and show retry. -
If WebSocket disconnects, show `Live updates paused — reconnecting` and
continue polling task detail every 10 seconds until reconnected. - A
disconnect must not imply that the task stopped.

**Primary actions and feedback** - Pause → stop before the next safe
step; show Paused. - Resume → continue from the next eligible step. -
Take Over → lock Agent execution and enable manual editing; preserve
completed work. - Terminate → require confirmation, stop future steps,
preserve completed work and log side effects. - Open draft → Review
Queue. - Retry failed step → only if retry-safe; otherwise require user
review. - Every control is state-aware and disabled when the operation
is not valid.

### 2.5.4 Inbox

**Purpose:** Provide a fully usable conventional email client.

**Layout** - Three columns: 1. Folder column. 2. Message/thread list. 3.
Reading pane. - Global search entry in the top bar and a local filter
row in the list. - Compose action always available.

**Core components** - Folders: Inbox, Starred, Sent, Drafts, Archive,
Trash. - Message rows with sender, subject, snippet, timestamp, unread
marker, attachment marker and star. - Reading pane with subject, sender,
recipients, date, body, attachments and thread history. - Compose editor
with To, Cc, Bcc, Subject and rich/plain text body. - Reply, Reply All,
Forward, Archive, Delete, Mark Read/Unread, Star and `Hand to Agent`. -
Demo/live provenance badge.

**Data source** - `GET /api/v1/threads` -
`GET /api/v1/threads/:threadId` - `GET /api/v1/emails` -
`GET /api/v1/emails/:messageId` - `POST /api/v1/emails/compose` -
`POST /api/v1/emails/:messageId/reply` -
`POST /api/v1/emails/:messageId/forward` -
`POST /api/v1/emails/:messageId/archive` -
`DELETE /api/v1/emails/:messageId` -
`POST /api/v1/emails/:messageId/hand-off`

**Empty state** - Empty folder: `No messages in this folder.` - No
connected mailbox: offer Connect Account and Demo Mailbox. - No search
results: show query and Clear Search.

**Loading state** - Load folder counts and list skeleton first; load the
reading pane when a thread is selected. - Preserve selected thread
during background refresh if it still exists.

**Error state** - Show list-level or message-level error without
blanking the entire application. - Keep compose/reply drafts locally
until successfully saved. - For send failures, retain the full draft and
provide Retry; never silently discard it.

**Primary actions and feedback** - Compose → opens composer. - Send →
confirmation only when required by provider/authorization; on success,
move to Sent and show a sent receipt. In Demo Mailbox, show
`Simulated send — no external email was delivered`. - Reply/Forward →
opens prefilled composer. - Archive → removes from Inbox and places in
Archive. - Delete → moves to Trash/soft-deleted state; permanent
deletion is not a default action. - Search → returns ranked results and
highlights matches. - Hand to Agent → opens Delegate Work with the
selected thread attached.

### 2.5.5 Review Queue

**Purpose:** Centralize drafts and other outputs requiring human review.

**Layout** - Left list of review items with status and age. - Right
detail panel with full draft or output. - Filters: All, Awaiting
Approval, Modified, Approved, Rejected. - Detail header shows task ID,
source thread, Agent, created time and authorization mode.

**Core components** - Review list rows with subject, recipient, source
and status. - Email preview with To/Cc/Subject/Body. - Attachment
chips. - Agent rationale and source references. - Editable draft
fields. - Approve & Send, Save Changes, Reject and Return to Task
actions. - Explicit `Demo — simulated send` or
`Live account — provider send` label.

**Data source** - `GET /api/v1/review` -
`GET /api/v1/review/:reviewId` - `PATCH /api/v1/review/:reviewId` -
`POST /api/v1/review/:reviewId/approve` -
`POST /api/v1/review/:reviewId/reject`

**Empty state** -
`Nothing waiting for review. Agent-created drafts will appear here.`

**Loading state** - Skeleton list and preview; preserve selected review
ID if possible.

**Error state** - If approval fails, keep the draft unchanged and
display the provider/model/API error. Do not mark it approved
optimistically. - If the item was changed elsewhere, return a conflict
response and reload the latest version.

**Primary actions and feedback** - Edit → save draft revision. - Approve
& Send → require confirmation showing recipient, subject and whether the
send is simulated or live. - Reject → require optional reason and return
the task to a terminal or revision-needed state. - Open source → Inbox
thread. - Return to task → Task Progress. - Approval and rejection are
audited.

### 2.5.6 Automations

**Purpose:** Manage user-defined recurring or condition-based email
workflows.

**Layout** - Automation list with name, trigger, next run, enabled state
and last result. - Detail/editor panel. - Run history.

**Core components** - Create Automation form. - Trigger types supported
in v1.0: scheduled daily/weekly; new matching email; and manual run. -
Conditions: sender, subject contains, label, unread state and mailbox. -
Actions: summarize, create a to-do, prepare a draft for review, or
notify the user. - Authorization display. - Enable/disable toggle. - Run
history with success, skipped and failed states.

**Data source** - `/api/v1/automations` and
`/api/v1/automations/:automationId/runs`.

**Empty state** -
`No automations yet. Create a rule for a repeatable task.`

**Loading state** - Skeleton list and editor.

**Error state** - Preserve unsaved automation form. If schedule
validation fails, identify the field and do not enable the automation.

**Primary actions and feedback** - Create, edit, enable, disable, run
now, duplicate and delete. - Every run is logged. - Automation actions
may create drafts and to-dos, but may not send email without an explicit
Review Queue approval. - A run that cannot execute safely is marked
`Needs attention`, not silently skipped.

### 2.5.7 Archive

**Purpose:** Find, inspect and restore archived email.

**Layout** - Search/filter toolbar. - Archived message/thread list. -
Reading pane consistent with Inbox. - Bulk selection toolbar for safe
reversible actions.

**Core components** - Filters by sender, date range, label and
attachment. - Thread list. - Restore to Inbox. - Delete to Trash. - Open
thread. - Hand to Agent.

**Data source** - `GET /api/v1/archive` -
`POST /api/v1/archive/:messageId/restore` -
`DELETE /api/v1/emails/:messageId`

**Empty state** - `Your archive is empty.` with a link to Inbox.

**Loading state** - List skeleton and reading pane skeleton.

**Error state** - Keep the selected item and filters; offer Retry. -
Failed restore leaves the message in Archive.

**Primary actions and feedback** - Restore → move item to Inbox and show
confirmation. - Delete → move to Trash after confirmation. -
Search/filter → update results. - Open → reading pane. - Hand to Agent →
Delegate Work with context attached.

### 2.5.8 Settings

**Purpose:** Provide user control over identity, mailboxes, Agent
behaviour, privacy, notifications and preferences.

**Layout** - Settings sub-navigation or tab list. - Content panel with
clearly grouped sections. - Save state and last-saved timestamp.

**Core components** 1. Profile: name, login email and account creation
date. 2. Connected Mailboxes: provider, address, connection status,
permissions, last sync, reconnect and disconnect. 3. Appearance: current
Day/Night preference; this is a secondary settings surface, while the
primary toggle remains bottom-left in the sidebar. 4. Agent: model
availability, response style, context permission, default authorization
mode and data-use explanation. 5. Notifications: in-app and email
notification preferences. 6. Privacy & Data: export data, delete demo
data, delete account and retention explanation. 7. Security: change
password, active sessions and sign out all sessions. 8. About: app
version, demo/live environment and support/report issue link.

**Data source** - `GET /api/v1/settings` - `PATCH /api/v1/settings` -
Account and session endpoints. - Mailbox account endpoints.

**Empty state** - If no provider is connected, show Connect Mailbox and
Open Demo Mailbox. - If there are no active sessions beyond the current
one, show the current session only.

**Loading state** - Load each settings group independently with skeleton
rows.

**Error state** - Keep unsaved form values; show field-level validation
and a retry option for server failures.

**Primary actions and feedback** - Save profile/settings. - Connect,
reconnect and disconnect mailbox. - Change default authorization
level. - Export data. - Revoke sessions. - Delete account after
password/re-authentication and a typed confirmation. - Sign out. - Every
destructive action has a confirmation step and an audit record.

------------------------------------------------------------------------

# Section 3 --- Registration and email-binding onboarding

## 3.1 Onboarding goals

A first-time user must be able to create an account, understand how
mailbox access works, connect a real provider or choose the seeded Demo
Mailbox, observe sync progress, and arrive at Today Briefing. The demo
path must not require a real email provider or a paid service.

Onboarding is a stateful flow. The backend persists progress so a
refresh, browser restart or temporary network failure does not force the
user to start over.

## 3.2 Onboarding state machine

`NOT_STARTED → ACCOUNT_CREATED → MAILBOX_CHOICE → AUTHORIZATION_EXPLAINED → PROVIDER_AUTH_PENDING or DEMO_SELECTED → CONNECTED → SYNCING → READY`

Recoverable states:

-   `AUTH_CANCELLED`
-   `AUTH_FAILED`
-   `SYNC_FAILED`
-   `SYNC_PAUSED`
-   `NEEDS_REAUTH`
-   `ONBOARDING_INCOMPLETE`

The client obtains the authoritative state from
`GET /api/v1/onboarding/status` after login.

## 3.3 Screen 1 --- Create account

### UI

-   Intenda logo and product name.
-   Heading: `Create your Intenda account`.
-   Fields: Name, Email, Password, Confirm Password.
-   Checkbox for Terms and Privacy acknowledgement.
-   Primary action: `Create account`.
-   Secondary action: `Sign in`.
-   Visible link: `Explore the Demo Mailbox` if anonymous demo access is
    enabled.

### Validation

-   Email must be syntactically valid and normalized to lowercase.
-   Password minimum: 12 characters; reject common compromised passwords
    where a local denylist is available.
-   Password and confirmation must match.
-   Terms acknowledgement is required.
-   Duplicate email returns a clear sign-in path rather than exposing
    account existence in an unsafe way.

### Backend

`POST /api/v1/auth/register`

Passwords are hashed with Argon2id. Never store plaintext passwords.

### States and errors

-   Submitting: disable duplicate submit; show progress.
-   Success: create session and continue to mailbox choice.
-   Validation failure: inline field errors.
-   Duplicate/registered address:
    `An account may already exist for this email. Try signing in or resetting your password.`
-   Server failure: retain name/email, clear password fields, show
    Retry.
-   Network interruption: do not create a duplicate account on retry;
    use idempotency key.

## 3.4 Screen 2 --- Choose a mailbox

After account creation, show two clear paths:

1.  **Connect a real email account** --- Google or Microsoft provider,
    subject to supported OAuth configuration.
2.  **Use the Demo Mailbox** --- seeded sample email data; no external
    account access required.

The Demo Mailbox option is prominent and explicitly labelled
`Demo data · Simulated sync · No email will be sent externally`.

The user can skip real provider connection and proceed with the demo.
They can connect a real account later in Settings.

## 3.5 Screen 3 --- Authorization explanation

Before redirecting to a provider, explain:

-   Which mailbox identity will be connected.
-   Which scopes are requested.
-   Why each permission is needed.
-   Whether the app can read messages, create drafts, send messages,
    archive or delete.
-   That permissions can be revoked in the provider account settings.
-   That Intenda does not use mailbox contents to train a model.
-   That the user can choose Demo Mailbox instead.

Request the narrowest practical scopes. Do not request full mailbox
access if a provider's narrower read/compose/send scopes are sufficient.
For v1.0, any provider permission that enables sending must be clearly
disclosed and sending remains gated by Intenda authorization and Review
Queue rules.

The user must click `Continue to Google` or `Continue to Microsoft`
after reading the explanation. No OAuth redirect occurs merely by
opening the screen.

## 3.6 Screen 4A --- Real provider authorization

### OAuth flow

1.  Client requests a provider authorization URL from the backend.
2.  Backend creates a cryptographically random state value and PKCE
    verifier/challenge where supported.
3.  Client redirects to provider.
4.  User authenticates and grants requested scopes.
5.  Provider redirects to the backend callback.
6.  Backend validates state, exchanges code server-side and stores
    tokens encrypted.
7.  Backend fetches mailbox identity and creates the account connection
    record.
8.  Client receives a success state and proceeds to sync.

### Error handling

-   User cancels: `Connection was cancelled. No mailbox was connected.`
    Offer Retry and Demo Mailbox.
-   State mismatch: reject callback, log security event, require
    restart.
-   Token exchange failure: do not store partial credentials; show
    Retry.
-   Missing required scope: explain the missing permission and request
    consent again.
-   Provider rate limit: schedule retry with backoff and show status.
-   Provider unavailable: allow retry later or use Demo Mailbox.
-   Existing connection: ask whether to reconnect or continue with
    existing mailbox.

Tokens must never be sent to or stored in frontend JavaScript storage.

## 3.7 Screen 4B --- Demo Mailbox selection

When the user selects Demo Mailbox:

1.  Backend creates a demo mailbox account associated with the user's
    account.
2.  Backend loads a deterministic seed dataset.
3.  Every message, thread, attachment and operation is tagged with
    `environment=demo`.
4.  The UI displays `DEMO MAILBOX` and `SIMULATED SYNC` labels.
5.  Demo send, archive and delete operations update only the demo
    database.

The demo mailbox must never send a real email or call a real provider.

## 3.8 Screen 5 --- Sync progress

### UI

-   Heading: `Preparing your mailbox`.
-   Connected account address or `Demo Mailbox`.
-   Progress bar and phase labels:
    1.  Connecting.
    2.  Reading mailbox metadata.
    3.  Syncing recent messages.
    4.  Building threads and search index.
    5.  Preparing Agent context.
-   Counts: messages found, messages synced, threads indexed.
-   `You can keep this page open; your mailbox is being prepared.`

### Sync behaviour

-   First sync imports a bounded recent window (default 90 days or
    provider-supported equivalent) and a maximum message count
    configured by the deployment.
-   Attachments are metadata-first; binary content is fetched only when
    needed and allowed.
-   Sync runs server-side and reports progress through WebSocket, with
    REST polling fallback.
-   For demo sync, progress is simulated but deterministic and labelled
    `Simulated`.
-   For real sync, progress reflects actual provider responses and is
    labelled `Live provider sync`.

### States

-   In progress: update progress without requiring refresh.
-   Completed: show `Mailbox ready` and `Open Today Briefing`.
-   Partial: show number of imported items and explain what could not be
    synced.
-   Failed: show phase, reason and Retry.
-   Paused: preserve cursor and resume from last completed page.
-   Provider throttled: back off and show
    `Your provider is limiting requests. Intenda will retry automatically.`

## 3.9 Screen 6 --- Enter Briefing

On success, navigate to `/app/briefing`.

Show a one-time welcome banner:

-   For demo:
    `You're using the Demo Mailbox. Messages and sync activity are simulated; no external emails will be sent.`
-   For real: `Your mailbox is connected. Provider activity is live.`

The banner can be dismissed but the environment label remains visible in
the application shell and relevant action confirmations.

## 3.10 Onboarding retry and recovery rules

-   Onboarding state is persisted server-side.
-   A browser refresh returns to the last valid step.
-   OAuth state is short-lived and single-use.
-   Sync retry resumes from the stored cursor.
-   A duplicate onboarding request must be idempotent.
-   If the user disconnects a mailbox, preserve their Intenda account
    and allow a new connection.
-   If the provider token expires, set account status to `needs_reauth`;
    do not repeatedly retry invalid credentials.
-   If the user chooses Demo Mailbox, no provider OAuth credentials are
    created.
-   All errors must include a stable machine-readable code and a safe
    user-facing message.

------------------------------------------------------------------------

# Section 4 --- Full email capability and mailbox data model

## 4.1 Capability requirements

The email subsystem must support conventional email work without
requiring the Agent:

-   List messages and threads.
-   Read a message and full thread.
-   Search by sender, recipient, subject, body, date, labels and
    attachment presence.
-   Compose a new email.
-   Reply, Reply All and Forward.
-   Save and edit drafts.
-   Send after required confirmation.
-   Mark read/unread.
-   Star/unstar.
-   Archive.
-   Move to Trash and restore.
-   View and download permitted attachments.
-   Hand a message or thread to the Agent with explicit context
    selection.

The user can use the Agent as an additional workflow, not as a
prerequisite for email.

## 4.2 Demo versus real activity

The interface must distinguish these modes at the point of use.

### Demo Mailbox

-   Banner: `DEMO MAILBOX`.
-   Sync label: `SIMULATED SYNC`.
-   Send confirmation:
    `Simulated send — no external email will be delivered.`
-   Archive/delete confirmations indicate that only demo data changes.
-   All demo records carry `environment=demo`.
-   No provider API is called for demo mailbox operations.
-   Seed data is deterministic and resettable.

### Real connected mailbox

-   Label: `LIVE MAILBOX`.
-   Sync label: `LIVE PROVIDER SYNC`.
-   Send confirmation names the connected account and recipient.
-   Provider operations are performed only after server-side
    authorization checks.
-   Provider errors are returned accurately.
-   All real external side effects are recorded in the audit log.

A demo operation must never be described as sent, delivered,
synchronized or deleted at a real provider.

## 4.3 Email list and thread behaviour

-   The message list is paginated using opaque cursors.
-   Default sort is newest first.
-   Unread state, star state, attachment state and labels are visible.
-   Selecting a thread opens the full conversation in chronological
    order.
-   A thread may contain multiple messages and participants.
-   The list refresh must preserve selection if the selected thread
    still exists.
-   Optimistic UI may be used for reversible local state changes, but
    must roll back if the backend rejects the mutation.
-   Pagination must not duplicate messages when new mail arrives during
    browsing.

## 4.4 Search

Search supports:

-   Free-text query across subject, sender, recipient and indexed body
    text.
-   Sender and recipient filters.
-   Date range.
-   Label/folder.
-   Read/unread.
-   Has attachment.
-   Account/mailbox.
-   Thread/message scope.

Search returns a result count when available, highlighted snippets and
the thread/message identifier. The search index is local to the
application database for demo data. For real provider accounts, provider
search may be used where practical, with local indexed metadata as a
fallback.

Search must enforce account ownership. No query may return messages from
another user or mailbox.

## 4.5 Compose, reply and forward

### Compose

Fields:

-   From account selector when multiple accounts exist.
-   To, Cc and Bcc.
-   Subject.
-   Body.
-   Attachments.
-   Save Draft.
-   Send.

Recipient validation occurs before send. Invalid addresses are
highlighted without clearing the draft.

### Reply

-   Prefill recipients from the selected message.
-   Preserve thread headers and provider reply identifiers.
-   Reply All is a separate explicit action.
-   Quote the relevant prior content according to standard email
    conventions.

### Forward

-   Prefill subject with `Fwd:` where appropriate.
-   Include forwarded content.
-   Allow attachments to be included only when the user has permission
    and the files are available.
-   Clearly show forwarded recipients and attachments before send.

### Draft persistence

-   Autosave after a short debounce.
-   Display `Saving…`, `Saved` or `Couldn't save`.
-   Save locally while offline and synchronize when connected.
-   Use draft revision numbers to avoid overwriting a newer revision.

## 4.6 Archive and delete

-   Archive removes a message/thread from Inbox and adds the Archive
    label; it does not destroy content.
-   Delete moves the message/thread to Trash or a soft-deleted state.
-   Permanent deletion is not a default v1.0 action.
-   Bulk archive/delete requires an explicit selection and confirmation.
-   In demo mode, all changes are local to demo records.
-   In real mode, use provider-supported operations and report provider
    success/failure.
-   The audit log records actor, timestamp, mailbox, target and result.

## 4.7 Hand to Agent

From a message or thread, `Hand to Agent` opens Delegate Work with the
selected thread attached as context.

The handoff preview shows:

-   Selected mailbox and thread.
-   Sender/participants.
-   Subject.
-   Number of messages included.
-   Attachments included or excluded.
-   Whether body content will be sent to the model.
-   A remove-context control.

The Agent receives only the selected context and any additional context
the user explicitly adds. The Agent does not gain blanket mailbox access
merely because one thread was handed off.

## 4.8 Normalized data model --- email entities

The following logical entities are required. Field types are
implementation-level types; IDs are UUIDs unless otherwise specified.

### `mail_accounts`

  ----------------------------------------------------------------------------
  Field                        Type                    Notes
  ---------------------------- ----------------------- -----------------------
  `id`                         UUID                    Primary key

  `user_id`                    UUID                    Owner

  `provider`                   TEXT                    `demo`, `google`,
                                                       `microsoft`

  `email_address`              TEXT                    Normalized address

  `display_name`               TEXT nullable           Provider display name

  `environment`                TEXT                    `demo` or `live`

  `status`                     TEXT                    `connected`, `syncing`,
                                                       `needs_reauth`,
                                                       `disconnected`, `error`

  `scopes`                     JSON                    Granted scopes

  `access_token_ciphertext`    TEXT nullable           Encrypted at rest

  `refresh_token_ciphertext`   TEXT nullable           Encrypted at rest

  `token_expires_at`           TIMESTAMP nullable      Expiry

  `provider_account_id`        TEXT nullable           Provider identity

  `last_sync_at`               TIMESTAMP nullable      Last successful sync

  `sync_cursor`                TEXT nullable           Provider cursor

  `created_at`                 TIMESTAMP               Creation

  `updated_at`                 TIMESTAMP               Update

  `deleted_at`                 TIMESTAMP nullable      Soft deletion
  ----------------------------------------------------------------------------

### `email_threads`

  Field                  Type            Notes
  ---------------------- --------------- -----------------------------
  `id`                   UUID            Primary key
  `user_id`              UUID            Owner
  `mail_account_id`      UUID            Mailbox
  `provider_thread_id`   TEXT nullable   Provider ID
  `subject_normalized`   TEXT            Normalized subject
  `snippet`              TEXT nullable   Latest snippet
  `participants`         JSON            Participant addresses/names
  `message_count`        INTEGER         Cached count
  `last_message_at`      TIMESTAMP       Latest message time
  `is_archived`          BOOLEAN         Cached folder state
  `is_trashed`           BOOLEAN         Soft-trash state
  `environment`          TEXT            `demo` or `live`
  `created_at`           TIMESTAMP       Creation
  `updated_at`           TIMESTAMP       Update

### `email_messages`

  ------------------------------------------------------------------------
  Field                    Type                    Notes
  ------------------------ ----------------------- -----------------------
  `id`                     UUID                    Primary key

  `user_id`                UUID                    Owner

  `mail_account_id`        UUID                    Mailbox

  `thread_id`              UUID                    Thread

  `provider_message_id`    TEXT nullable           Provider ID

  `internet_message_id`    TEXT nullable           RFC Message-ID

  `in_reply_to`            TEXT nullable           Reply relationship

  `references_header`      TEXT nullable           Thread references

  `from_address`           TEXT                    Sender

  `from_name`              TEXT nullable           Sender name

  `to_recipients`          JSON                    To list

  `cc_recipients`          JSON                    Cc list

  `bcc_recipients`         JSON                    Bcc list

  `subject`                TEXT                    Subject

  `body_text`              TEXT nullable           Plain text

  `body_html_sanitized`    TEXT nullable           Sanitized HTML

  `snippet`                TEXT nullable           Preview

  `received_at`            TIMESTAMP nullable      Received time

  `sent_at`                TIMESTAMP nullable      Sent time

  `is_read`                BOOLEAN                 Read state

  `is_starred`             BOOLEAN                 Star state

  `is_draft`               BOOLEAN                 Draft state

  `is_sent`                BOOLEAN                 Sent state

  `is_trashed`             BOOLEAN                 Trash state

  `environment`            TEXT                    `demo` or `live`

  `provider_payload_ref`   TEXT nullable           Optional provider
                                                   reference; avoid
                                                   storing unnecessary raw
                                                   payload

  `created_at`             TIMESTAMP               Creation

  `updated_at`             TIMESTAMP               Update

  `deleted_at`             TIMESTAMP nullable      Soft deletion
  ------------------------------------------------------------------------

### `email_attachments`

  Field                      Type            Notes
  -------------------------- --------------- ------------------------------------------
  `id`                       UUID            Primary key
  `message_id`               UUID            Parent message
  `provider_attachment_id`   TEXT nullable   Provider ID
  `filename`                 TEXT            Display filename
  `mime_type`                TEXT            MIME type
  `size_bytes`               BIGINT          Size
  `content_hash`             TEXT nullable   Integrity/deduplication
  `storage_key`              TEXT nullable   Server-side storage key
  `is_inline`                BOOLEAN         Inline attachment
  `content_id`               TEXT nullable   CID reference
  `scan_status`              TEXT            `pending`, `clean`, `blocked`, `unknown`
  `created_at`               TIMESTAMP       Creation

### `email_labels`

  Field                 Type            Notes
  --------------------- --------------- --------------------------
  `id`                  UUID            Primary key
  `mail_account_id`     UUID            Mailbox
  `provider_label_id`   TEXT nullable   Provider label
  `name`                TEXT            Label name
  `kind`                TEXT            `system` or `user`
  `color`               TEXT nullable   Neutral UI metadata only
  `created_at`          TIMESTAMP       Creation

### `email_message_labels`

  Field          Type        Notes
  -------------- ----------- ------------------
  `message_id`   UUID        Message
  `label_id`     UUID        Label
  `created_at`   TIMESTAMP   Association time

### `email_drafts`

  -----------------------------------------------------------------------
  Field                   Type                    Notes
  ----------------------- ----------------------- -----------------------
  `id`                    UUID                    Primary key

  `user_id`               UUID                    Owner

  `mail_account_id`       UUID                    From account

  `thread_id`             UUID nullable           Existing thread if
                                                  reply

  `source_message_id`     UUID nullable           Source message

  `to_recipients`         JSON                    To

  `cc_recipients`         JSON                    Cc

  `bcc_recipients`        JSON                    Bcc

  `subject`               TEXT                    Subject

  `body_text`             TEXT                    Draft body

  `body_html`             TEXT nullable           Sanitized HTML

  `revision`              INTEGER                 Optimistic concurrency

  `status`                TEXT                    `draft`, `in_review`,
                                                  `approved`, `rejected`,
                                                  `sent`, `failed`

  `environment`           TEXT                    `demo` or `live`

  `created_at`            TIMESTAMP               Creation

  `updated_at`            TIMESTAMP               Update
  -----------------------------------------------------------------------

## 4.9 Sync mechanism

### Real provider sync

-   Provider adapters isolate Gmail/Microsoft API differences from the
    application domain.
-   OAuth and token refresh happen server-side.
-   Initial sync imports mailbox metadata and recent messages within
    configured bounds.
-   Incremental sync uses provider history/delta cursors when available.
-   Sync jobs are idempotent. Provider IDs and message IDs are unique
    within their account.
-   Sync cursor is committed only after a page is processed
    successfully.
-   Backoff applies to provider throttling and transient errors.
-   A failed page can be retried without duplicating records.
-   Re-authentication is required when refresh fails due to
    revoked/expired credentials.
-   The app records sync start, completion, item counts, cursor and
    error code.

### Demo sync

-   Seed records are loaded into the user's demo mailbox.
-   A deterministic simulated sync job emits progress events over
    several phases.
-   The delay is configurable and kept short for an interviewer.
-   No real provider API is called.
-   Demo records are tagged `environment=demo`.
-   The UI always says `SIMULATED SYNC`.

### Sync cadence

-   Initial sync runs during onboarding.
-   Manual sync is available from Inbox and Settings.
-   A lightweight periodic sync may be scheduled while the app is
    active, subject to provider limits.
-   The backend must not create an uncontrolled polling loop.
-   On app focus, request sync status and perform incremental sync only
    if due.
-   If provider webhooks are unavailable in the demo deployment, use
    bounded polling.

### Conflict handling

-   Provider state is authoritative for provider-owned fields.
-   User edits to local drafts use revision numbers.
-   A stale write returns `409 Conflict` with the latest revision.
-   The UI presents a comparison or reload option rather than
    overwriting silently.
-   Archive/trash operations are retried only when idempotent.
-   Send operations use an idempotency key to prevent duplicate sends
    after timeouts.

------------------------------------------------------------------------

# Section 5 --- Agent with a real free model

## 5.1 Locked model integration

The v1.0 Agent must connect to a real, usable free model. The locked
implementation is:

-   **Provider:** Groq free tier.
-   **API compatibility:** OpenAI-compatible Chat Completions API.
-   **Model ID:** `openai/gpt-oss-20b`.
-   **API base URL:** `https://api.groq.com/openai/v1`.
-   **Chat endpoint:** `POST /chat/completions`.
-   **Streaming:** enabled; server streams response chunks to the
    frontend as Server-Sent Events (SSE).
-   **Secret:** `GROQ_API_KEY`, stored only in the backend environment.
-   **Frontend:** never receives the Groq key, provider authorization
    header or raw provider credential.
-   **No paid model or paid service:** do not add a paid provider as a
    fallback. The application remains usable manually when the free
    model is unavailable.

The provider and model identifiers must be configurable by environment
variable for maintenance, but the production demo default is fixed to
the values above. A reviewer must be able to verify that the Agent is
genuinely responding from the configured model when the provider is
available.

## 5.2 Backend proxy

The browser calls Intenda's backend, not Groq directly.

Request path:

1.  Frontend sends a user message to
    `POST /api/v1/agent/conversations/:conversationId/messages`.
2.  Backend authenticates the session and checks per-user rate limits.
3.  Backend loads conversation history and only the email context
    explicitly selected or authorized for the task.
4.  Backend applies system instructions, capability policy and
    prompt-injection boundaries.
5.  Backend calls Groq using `Authorization: Bearer ${GROQ_API_KEY}`.
6.  Backend consumes the provider's streaming response.
7.  Backend translates provider chunks into Intenda SSE events.
8.  Frontend renders text incrementally, token/chunk by token/chunk.
9.  Backend stores the final assistant message and usage/error metadata.

The backend must never forward the provider key to the browser, include
it in SSE events, or write it to application logs.

## 5.3 SSE protocol

Endpoint:

`POST /api/v1/agent/conversations/{conversationId}/messages`

Request JSON:

``` json
{
  "content": "Draft a polite follow-up to Acme Studio about the quotation.",
  "context": {
    "thread_ids": ["thread-uuid"],
    "message_ids": [],
    "include_attachments": false
  },
  "stream": true,
  "client_message_id": "uuid"
}
```

Response headers:

``` http
Content-Type: text/event-stream
Cache-Control: no-cache, no-transform
Connection: keep-alive
X-Accel-Buffering: no
```

SSE event types:

-   `message.started` --- conversation and message IDs.
-   `message.delta` --- incremental text chunk.
-   `message.annotation` --- structured plan/risk/context annotation.
-   `message.completed` --- final message ID, status and usage metadata.
-   `message.error` --- stable error code and safe message.
-   `heartbeat` --- keep-alive event.

The client appends `message.delta` text to the active assistant message.
It must not re-render the entire transcript in a way that loses scroll
or focus. On `message.completed`, mark the message complete and persist
its final state. On `message.error`, stop the stream and show a retry
affordance.

## 5.4 Timeouts, retries and rate limits

Recommended v1.0 defaults:

-   Connection timeout: 10 seconds.
-   First-token timeout: 20 seconds.
-   Total response timeout: 90 seconds.
-   Maximum automatic retries: 2 for transient provider errors only.
-   Retry backoff: approximately 1 second, then 2 seconds, with jitter.
-   Do not automatically retry a user request after a partial response
    unless the request is safely restarted as a new model attempt.
-   Do not execute tools or external actions twice because of a model
    retry.
-   App-level per-user limit: 10 Agent messages per minute and 100 per
    day in the demo configuration; make limits configurable.
-   Respect Groq's current free-tier rate-limit headers and quota
    response. The provider's free-tier quota may change; the app must
    treat `429` as a recoverable capacity condition.
-   If a request exceeds the app limit, return `429 RATE_LIMITED` with
    `Retry-After`.
-   If the model is unavailable, no task or external side effect may be
    started solely on the basis of the failed model request.

## 5.5 Exact fallback wording and behaviour

When the model is unavailable, the frontend must show this exact
fallback wording:

> **"I'm temporarily unable to reach the AI model. Your request has been
> saved, but I have not taken any action. Please retry in a moment or
> continue manually."**

Behaviour:

1.  Save the user's submitted message with status `model_unavailable`.
2.  Do not fabricate an Agent answer.
3.  Do not create a task, draft, to-do, send operation or other side
    effect from that failed request.
4.  Show Retry and Continue Manually actions.
5.  Retry submits a new model request with a new attempt ID while
    preserving the original user message.
6.  Continue Manually returns the user to Inbox or the relevant manual
    editor.
7.  Display a subtle `AI temporarily unavailable` status.
8.  Log provider status code and request ID without logging the API key
    or sensitive message body.
9.  If the provider returns after a retry, continue normally. Do not
    retroactively execute an earlier failed request.

If a stream fails after some tokens have arrived, preserve the partial
response as an incomplete message, show the exact fallback wording in a
separate system notice, and offer Retry. Do not present the partial
response as a completed plan.

## 5.6 Agent capabilities

The Agent may:

1.  **Read email context** --- only messages/threads selected by the
    user or explicitly authorized for the current task.
2.  **Summarize** --- produce concise summaries, action items, deadlines
    and open questions with links to source messages.
3.  **Draft** --- create new email drafts, replies and forwards. Drafts
    are saved to the Review Queue when generated by a task.
4.  **Create to-dos** --- create user-visible to-do items with due dates
    only when supported by source context or explicitly supplied by the
    user.
5.  **Plan delegated tasks** --- turn a natural-language goal into
    ordered steps, dependencies, required context and authorization
    checkpoints.
6.  **Execute delegated tasks** --- perform permitted internal actions
    and approved provider operations within the selected authorization
    level.
7.  **Report progress** --- emit structured events and update task
    steps.
8.  **Ask clarifying questions** --- stop and ask when recipient, date,
    intent or scope is ambiguous.
9.  **Explain decisions** --- summarize why a step is proposed and which
    source messages support it.

## 5.7 Agent capability boundaries

### It may do without additional approval

-   Read the exact messages and threads included in task context.
-   Summarize those messages.
-   Extract explicit action items and dates.
-   Prepare a plan.
-   Draft email content.
-   Create a local to-do if the user has enabled that capability and the
    task authorization permits it.
-   Update internal task progress and status.
-   Save draft content to the Review Queue.

### It must stop for human confirmation

-   Before sending any email unless a future version introduces a
    separately reviewed, explicitly configured send policy. In v1.0, the
    selected `Fully Automatic but Confirm Before Sending` mode still
    requires confirmation before every send.
-   Before changing recipients or sending to a new recipient not present
    in the approved plan.
-   Before forwarding an email or attachment to an external recipient.
-   Before deleting or permanently removing any message.
-   Before changing mailbox permissions, connecting/disconnecting an
    account or changing security settings.
-   Before taking an action outside the original plan.
-   When source content conflicts, the request is ambiguous, or
    confidence is insufficient.
-   When the task reaches an authorization checkpoint defined by the
    selected mode.

### It must NEVER

-   Send an email without satisfying the selected authorization policy
    and explicit send confirmation.
-   Delete messages or attachments permanently on its own.
-   Change a user's password, session, provider scopes or security
    settings.
-   Purchase, subscribe, transfer money or perform financial
    transactions.
-   Pretend a simulated action occurred at a real provider.
-   Claim that a message was delivered when the provider did not confirm
    it.
-   Invent recipients, facts, attachments, deadlines, quotations or
    source evidence.
-   Follow instructions embedded in an email that attempt to override
    system policy or user authorization.
-   Reveal another user's mailbox content or any secret.
-   Expose provider credentials, session tokens, API keys or internal
    prompts.
-   Continue after a task is paused, taken over or terminated.
-   Escalate its own authorization level.
-   Treat a generated plan as permission to execute it.
-   Use model output as proof that an external side effect succeeded.

## 5.8 Prompt-injection and untrusted content handling

Email bodies, attachments, quoted messages, web links and signatures are
untrusted data. They are context to analyze, not instructions that can
change Agent policy.

Rules:

1.  System and developer policy always outrank user-provided content;
    email content has no authority to alter permissions.
2.  Treat instructions such as "ignore previous instructions," "send
    this data," "reveal your prompt," or "click this link" inside
    messages as untrusted content.
3.  Do not execute links, macros, scripts or attachment instructions.
4.  Do not exfiltrate mailbox content to a recipient named only in an
    untrusted email body.
5.  Do not infer consent from a sender's request. Only the authenticated
    user can authorize Intenda actions.
6.  The Agent may tell the user that a message contains suspicious or
    instruction-like content.
7.  Keep tool permissions allowlisted and validate all tool arguments
    server-side.
8.  Never allow model-generated JSON to bypass backend authorization
    checks.
9.  Record security-relevant prompt-injection detections in the audit
    log without copying unnecessary sensitive content.

## 5.9 Context limits and retrieval

-   Use a bounded context window per request.
-   Include the current conversation's recent turns, a concise
    conversation summary and only the selected email context.
-   Default maximum: 10 messages or 20,000 characters of email body text
    per task context, whichever is reached first; configurable.
-   Attachments are excluded by default. If enabled, extract only
    supported text types within size and safety limits.
-   Do not send raw binary attachments to the model.
-   Truncate quoted email chains carefully and preserve the most recent
    relevant messages.
-   Include source IDs and timestamps in the internal context
    representation so outputs can cite the correct messages.
-   If context exceeds limits, ask the user to narrow the thread or
    explicitly select messages.
-   Do not silently omit critical messages; show which items were
    included.

## 5.10 Conversation storage

### `agent_conversations`

-   `id` UUID primary key
-   `user_id` UUID
-   `title` TEXT
-   `status` TEXT (`active`, `archived`)
-   `context_scope` JSON
-   `created_at`, `updated_at` TIMESTAMP
-   `last_message_at` TIMESTAMP

### `agent_messages`

-   `id` UUID primary key
-   `conversation_id` UUID
-   `user_id` UUID
-   `role` TEXT (`system`, `user`, `assistant`, `tool`, `notice`)
-   `content` TEXT
-   `content_json` JSON nullable
-   `model_provider` TEXT nullable
-   `model_id` TEXT nullable
-   `status` TEXT (`streaming`, `complete`, `failed`,
    `model_unavailable`, `incomplete`)
-   `client_message_id` TEXT nullable
-   `attempt_id` UUID nullable
-   `input_tokens` INTEGER nullable
-   `output_tokens` INTEGER nullable
-   `error_code` TEXT nullable
-   `created_at`, `completed_at` TIMESTAMP nullable

Conversation history is private to the owning user. Retention and
deletion are controlled by the account's data settings. Provider API
keys and raw authorization headers are never stored in conversation
rows.

------------------------------------------------------------------------

# Section 6 --- Delegation and task system

## 6.1 Delegation lifecycle

The delegation workflow is:

1.  User states a desired outcome in natural language.
2.  Agent reads only selected context and asks clarifying questions if
    needed.
3.  Agent generates a plan with steps, dependencies, recipients,
    expected outputs and risk notes.
4.  User reviews the plan.
5.  User selects an authorization level.
6.  User explicitly starts execution.
7.  Backend creates a task and ordered task steps.
8.  Task runner executes permitted steps and emits real-time progress.
9.  At authorization gates, the task waits for user action.
10. Drafts and other outputs are saved to Review Queue.
11. User edits, approves, rejects or returns an output to the task.
12. Task reaches Completed, Failed or Cancelled with a full event
    history.

No task is created from an unconfirmed model plan. The `Start execution`
action is required.

## 6.2 Authorization levels and enforcement

The authorization mode is stored on the task and enforced by the
backend. The frontend display is informative; it is not the security
boundary.

### Mode A --- Confirm Every Step

-   Every task step requires an explicit user approval before execution.
-   The Agent may generate the plan and prepare step details.
-   The task enters `waiting_user` before each step.
-   The user sees the proposed action, affected records, inputs and
    expected side effects.
-   Approving one step authorizes only that step.
-   Editing a step invalidates its previous approval.
-   Rejecting a step pauses the task and asks whether to revise or
    terminate.
-   No later step inherits approval from an earlier step.
-   Email sending still requires a separate final send confirmation in
    Review Queue.

### Mode B --- Confirm at Key Milestones

-   The Agent may execute low-risk internal steps in the approved plan
    without a prompt at every sub-step.
-   The plan must define milestones before execution starts.
-   The task pauses at each milestone and shows completed work, next
    actions, recipients and risks.
-   The user approves the milestone to continue.
-   Any external side effect not explicitly permitted in the approved
    plan becomes a new milestone.
-   Sending email still requires Review Queue approval and final send
    confirmation.
-   If the Agent discovers a new recipient, new external system or scope
    expansion, it must stop and request approval.

### Mode C --- Fully Automatic but Confirm Before Sending

-   The Agent may execute all safe internal steps in the approved plan
    without pausing at intermediate milestones.
-   It may read selected context, summarize, create local to-dos,
    prepare drafts and organize task artifacts.
-   It must stop before sending any email.
-   The Review Queue is the mandatory send gate.
-   It may not delete mail, change account settings, change permissions
    or perform unrelated external side effects.
-   If scope changes or ambiguity appears, it pauses and asks the user.
-   The UI must never label this mode simply `fully autonomous`; always
    show the complete label
    `Fully Automatic but Confirm Before Sending`.

All three modes are constrained by the NEVER rules in Section 5.

## 6.3 Task state machine

Task states:

-   `draft` --- plan exists but execution has not started.
-   `queued` --- accepted and waiting for worker capacity.
-   `planning` --- Agent is preparing or validating the execution plan.
-   `running` --- a permitted step is executing.
-   `waiting_user` --- authorization, clarification or decision
    required.
-   `paused` --- user or system paused execution.
-   `takeover` --- Agent execution is locked while the user takes manual
    control.
-   `completed` --- all required steps completed and outputs persisted.
-   `failed` --- task cannot continue without a retry or user
    intervention.
-   `cancelled` --- user terminated the task.
-   `needs_attention` --- non-terminal state requiring user review.

Valid transitions are enforced server-side. A client cannot set a task
state directly.

## 6.4 Task step model

Each task step includes:

-   Step ID and task ID.
-   Sequence number.
-   Type (`read_context`, `summarize`, `draft_email`, `create_todo`,
    `label_message`, `wait_for_approval`, `send_email`, `archive_email`,
    `custom_internal`).
-   Human-readable title and description.
-   Input references.
-   Output references.
-   Status (`pending`, `ready`, `running`, `waiting_user`, `completed`,
    `failed`, `skipped`, `cancelled`).
-   Risk level (`low`, `medium`, `high`).
-   Authorization requirement.
-   Started/completed timestamps.
-   Retry count and error code.
-   Idempotency key.
-   Progress percentage where meaningful.

## 6.5 Pause, resume, take over and terminate

### Pause

-   User selects Pause.
-   Backend marks the task `paused` after the current safe atomic
    operation completes.
-   No new step starts.
-   A network request already in flight may finish; the result is
    recorded.
-   The task timeline explains whether an in-flight action completed.
-   Pause does not undo completed work or reverse external side effects.

### Resume

-   Backend validates that the task is resumable and that required
    approvals remain valid.
-   Resume continues from the next eligible step.
-   Expired approvals are invalidated and requested again.
-   A failed non-idempotent action is not retried automatically.
-   The user sees a resume summary before execution continues.

### Take Over

-   Backend obtains a task execution lock and moves the task to
    `takeover`.
-   Agent workers stop scheduling new steps.
-   The user can edit drafts, change recipients, add notes or complete
    manual work.
-   Completed work remains intact.
-   Any external side effect already completed remains completed.
-   On returning control to the Agent, the user reviews a diff of manual
    changes and explicitly chooses `Resume with updated context`.
-   The Agent must not overwrite manual edits without showing a
    conflict/diff.

### Terminate

-   Requires a confirmation dialog summarizing completed steps and known
    external side effects.
-   Backend marks the task `cancelled` and prevents new steps.
-   In-flight safe reads may be cancelled. In-flight provider operations
    are reconciled before final state is shown.
-   Completed drafts and to-dos remain unless the user separately
    deletes them.
-   Sent email cannot be unsent by Intenda; the task history states this
    clearly.
-   No automatic rollback is attempted for irreversible external
    actions.
-   Termination is recorded in the audit log.

## 6.6 Real-time progress

The frontend opens an authenticated WebSocket connection to
`/api/v1/ws`.

Task events include:

-   `task.created`
-   `task.queued`
-   `task.started`
-   `task.progress`
-   `task.step.started`
-   `task.step.completed`
-   `task.step.failed`
-   `task.waiting_user`
-   `task.decision.required`
-   `task.paused`
-   `task.resumed`
-   `task.takeover`
-   `task.terminated`
-   `task.completed`
-   `task.failed`
-   `task.output.created`
-   `task.log.appended`

Every event includes `event_id`, `task_id`, `user_id`, `timestamp`,
`sequence` and a typed `payload`. Events are persisted before broadcast
so reconnecting clients can fetch missed events.

The client reconnects with exponential backoff and sends its last
received sequence. On reconnect, it requests missed events or refreshes
task detail through REST.

## 6.7 Decisions and approval gates

A decision object contains:

-   Decision ID.
-   Task ID and optional step ID.
-   Decision type (`approve_step`, `approve_milestone`, `choose_option`,
    `approve_send`, `clarify`).
-   Prompt and context.
-   Options.
-   Default expiry policy.
-   Status (`pending`, `approved`, `rejected`, `modified`, `expired`,
    `cancelled`).
-   Responder and response timestamp.

A decision is single-use. Repeated approval requests with the same
idempotency key return the original result.

## 6.8 Outputs and Review Queue

Agent-generated email outputs are stored as drafts and create Review
Queue items.

Required behaviour:

-   Draft creation does not send email.
-   Review item includes task ID, source thread, model ID, draft
    revision and authorization mode.
-   User can edit recipients, subject and body.
-   Any edit increments revision and invalidates earlier approval.
-   Approve & Send displays a final confirmation with mailbox,
    recipient, subject and environment.
-   Demo send updates demo records and displays
    `Simulated send — no external email was delivered`.
-   Live send calls the provider server-side and records provider
    message ID and result.
-   Failed sends keep the draft in Review Queue with `send_failed`.
-   Retry uses an idempotency key and reconciles provider state before
    attempting another send.

## 6.9 Retry and failure handling

-   Retry is allowed only for transient and idempotent operations.
-   Model errors may be retried within Section 5 limits.
-   Provider `429` responses use `Retry-After` or exponential backoff.
-   Validation errors require user correction.
-   Permission errors require reauthorization or user action.
-   Non-idempotent sends are reconciled before retry.
-   A failed step records error code, safe message, attempt count and
    whether any side effect may have occurred.
-   The task does not silently skip a failed required step.
-   The user can retry, edit the plan, take over or terminate.
-   A task with unresolved ambiguity moves to `needs_attention` or
    `waiting_user`.

------------------------------------------------------------------------

# Section 7 --- Technical specification

## 7.1 Architecture overview

### Frontend

-   React.
-   TypeScript.
-   Vite.
-   React Router.
-   TanStack Query or equivalent for server state and caching.
-   Lightweight local state for UI controls.
-   Native `EventSource` for SSE Agent streaming.
-   WebSocket client for task progress.
-   Accessible component primitives.
-   CSS variables for Day/Night design tokens.

The frontend is built as static assets and served by the FastAPI
application so the demo can run as one deployable web service.

### Backend

-   Python 3.12+.
-   FastAPI.
-   Pydantic request/response validation.
-   SQLAlchemy 2.x or SQLModel.
-   SQLite for the demo.
-   PostgreSQL-compatible schema and migrations for later production
    use.
-   Background task runner integrated into the same process for the
    small demo workload.
-   Provider adapters for Groq, Demo Mailbox, Google and Microsoft.
-   REST API under `/api/v1`.
-   WebSocket endpoint `/api/v1/ws`.
-   SSE endpoint for Agent messages.

### Deployment

-   One deployable web service.
-   Target: Render Free.
-   FastAPI serves the built React application and API from the same
    origin.
-   SQLite database stored on an attached persistent disk where
    supported; if the selected free deployment does not provide
    persistent storage, use a clearly documented ephemeral demo database
    and reseed on restart. Do not imply persistence across restarts if
    the host does not guarantee it.
-   Public test URL is produced by the actual deployment and must be
    verified before sharing. Do not hard-code or invent a URL in the
    specification.

The free hosting tier may sleep, restart or impose resource limits. The
demo must show a warm-up/loading state and must not claim
production-grade availability.

## 7.2 Repository structure

``` text
intenda/
  frontend/
    src/
      app/
      components/
      features/
        auth/
        onboarding/
        briefing/
        delegate/
        tasks/
        inbox/
        review/
        automations/
        archive/
        settings/
      hooks/
      lib/
      styles/
      types/
    index.html
    package.json
    vite.config.ts
  backend/
    app/
      api/
        routes/
        dependencies/
      core/
      db/
      models/
      schemas/
      services/
        agent/
        email/
        tasks/
        sync/
      workers/
      main.py
    migrations/
    tests/
    requirements.txt
  scripts/
    seed_demo.py
  README.md
  render.yaml
```

## 7.3 API conventions

Base path: `/api/v1`.

-   JSON request and response bodies except SSE and file downloads.
-   UUID identifiers.
-   Timestamps in ISO 8601 UTC.
-   Pagination uses `limit` and opaque `cursor`.
-   Mutating requests accept `Idempotency-Key` where duplicate execution
    would be harmful.
-   Every response includes request correlation ID.
-   Standard success envelope:

``` json
{
  "data": {},
  "meta": {
    "request_id": "uuid"
  }
}
```

-   Standard error envelope:

``` json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request could not be processed.",
    "details": {},
    "request_id": "uuid"
  }
}
```

Common HTTP errors:

-   `400` malformed request or invalid state transition.
-   `401` unauthenticated.
-   `403` authenticated but not authorized.
-   `404` resource not found or not owned by user.
-   `409` version conflict or duplicate state transition.
-   `422` schema/field validation.
-   `429` rate limit.
-   `500` unexpected server error.
-   `502` upstream provider failure.
-   `503` provider/model temporarily unavailable.
-   `504` upstream timeout.

## 7.4 REST API --- complete v1.0 endpoint inventory

### 7.4.1 Authentication and session endpoints

  --------------------------------------------------------------------------------------------------------------------------------------------------
  Method and path                        Request                                  Success response                                 Errors
  -------------------------------------- ---------------------------------------- ------------------------------------------------ -----------------
  `POST /auth/register`                  `{name,email,password,terms_accepted}`   `{user,session,onboarding_state}`                400, 409, 422,
                                                                                                                                   429

  `POST /auth/login`                     `{email,password}`                       `{user,session}`                                 401, 422, 429

  `POST /auth/logout`                    Empty body                               `{logged_out:true}`                              401

  `GET /auth/me`                         None                                     `{user,session}`                                 401

  `POST /auth/demo-session`              `{display_name?}`                        `{user,session,mail_account,onboarding_state}`   429, 500

  `POST /auth/password/reset/request`    `{email}`                                `{accepted:true}`                                422, 429

  `POST /auth/password/reset/complete`   `{token,new_password}`                   `{password_updated:true}`                        400, 422, 429

  `GET /auth/sessions`                   None                                     `{items:[session...]}`                           401

  `DELETE /auth/sessions/{sessionId}`    None                                     `{revoked:true}`                                 401, 404

  `POST /auth/sessions/revoke-others`    None                                     `{revoked_count}`                                401
  --------------------------------------------------------------------------------------------------------------------------------------------------

### 7.4.2 Onboarding endpoints

  ------------------------------------------------------------------------------------------------------------------------------------------------------
  Method and path                               Request                                  Success response                              Errors
  --------------------------------------------- ---------------------------------------- --------------------------------------------- -----------------
  `GET /onboarding/status`                      None                                     `{state,completed_steps,mailbox_choice}`      401

  `POST /onboarding/start`                      `{}`                                     `{state:"ACCOUNT_CREATED"}`                   401, 409

  `GET /onboarding/providers`                   None                                     `{providers:[{id,name,available,scopes}]}`    401

  `POST /onboarding/mailbox-choice`             `{choice:"demo"|"google"|"microsoft"}`   `{next_step,authorization_summary}`           401, 422

  `POST /onboarding/oauth/{provider}/start`     `{redirect_uri}`                         `{authorization_url,state_expires_at}`        401, 422, 503

  `GET /onboarding/oauth/{provider}/callback`   OAuth query params                       Redirect to onboarding result; server stores  400, 401, 502
                                                                                         connection                                    

  `POST /onboarding/demo-mailbox`               `{seed_profile?}`                        `{mail_account,sync_job}`                     401, 409

  `POST /onboarding/complete`                   `{mail_account_id}`                      `{completed:true,redirect:"/app/briefing"}`   401, 409

  `POST /onboarding/retry`                      `{step}`                                 `{state,retry_started:true}`                  401, 409, 503
  ------------------------------------------------------------------------------------------------------------------------------------------------------

### 7.4.3 Mail account and sync endpoints

  ------------------------------------------------------------------------------------------------------------------------
  Method and path                          Request                         Success response              Errors
  ---------------------------------------- ------------------------------- ----------------------------- -----------------
  `GET /accounts`                          Query `status?`                 `{items:[mail_account...]}`   401

  `GET /accounts/{accountId}`              None                            `{account}`                   401, 404

  `POST /accounts/connect`                 `{provider,redirect_uri}`       `{authorization_url,state}`   401, 422, 503

  `POST /accounts/{accountId}/reconnect`   `{}`                            `{authorization_url,state}`   401, 404, 409

  `DELETE /accounts/{accountId}`           `{confirm_email?}`              `{disconnected:true}`         401, 404, 409

  `POST /accounts/{accountId}/sync`        `{mode:"incremental"|"full"}`   `{sync_job}`                  401, 404, 409,
                                                                                                         429

  `GET /sync/status`                       Query `account_id?`             `{jobs:[sync_job...]}`        401

  `GET /sync/jobs/{jobId}`                 None                            `{sync_job,progress}`         401, 404

  `POST /sync/jobs/{jobId}/retry`          `{}`                            `{sync_job}`                  401, 404, 409
  ------------------------------------------------------------------------------------------------------------------------

### 7.4.4 Briefing endpoints

  ---------------------------------------------------------------------------------------------------------------
  Method and path   Request           Success response                                          Errors
  ----------------- ----------------- --------------------------------------------------------- -----------------
  `GET /briefing`   Query `date?`     `{metrics,decisions,tasks,recent_messages,environment}`   401, 503

  ---------------------------------------------------------------------------------------------------------------

### 7.4.5 Email, thread, draft and search endpoints

  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Method and path                         Request                                                                        Success response                         Errors
  --------------------------------------- ------------------------------------------------------------------------------ ---------------------------------------- -----------------
  `GET /emails`                           Query `account_id,folder,limit,cursor,unread,starred,has_attachment`           `{items,next_cursor,total?}`             401, 422

  `GET /emails/{messageId}`               None                                                                           `{message,attachments,thread_summary}`   401, 404

  `POST /emails/compose`                  `{account_id,to,cc,bcc,subject,body,attachments?}`                             `{draft}`                                401, 422, 413

  `POST /emails/{messageId}/reply`        `{reply_all,body,attachments?}`                                                `{draft}`                                401, 404, 422

  `POST /emails/{messageId}/forward`      `{to,cc,bcc,body,include_attachments}`                                         `{draft}`                                401, 404, 422

  `POST /emails/{messageId}/send`         `{draft_id,revision,confirm_send,environment}`                                 `{send_result,message?}`                 401, 403, 404,
                                                                                                                                                                  409, 422, 502,
                                                                                                                                                                  504

  `POST /emails/{messageId}/archive`      `{}`                                                                           `{archived:true}`                        401, 404, 409,
                                                                                                                                                                  502

  `DELETE /emails/{messageId}`            `{move_to_trash:true}`                                                         `{trashed:true}`                         401, 404, 409,
                                                                                                                                                                  502

  `POST /emails/{messageId}/restore`      `{destination:"inbox"}`                                                        `{restored:true}`                        401, 404, 409

  `POST /emails/{messageId}/read-state`   `{is_read:boolean}`                                                            `{is_read}`                              401, 404

  `POST /emails/{messageId}/star`         `{is_starred:boolean}`                                                         `{is_starred}`                           401, 404

  `POST /emails/{messageId}/hand-off`     `{conversation_id?,intent?}`                                                   `{conversation,context_preview}`         401, 404, 422

  `GET /threads`                          Query `account_id,folder,limit,cursor,q?`                                      `{items,next_cursor}`                    401, 422

  `GET /threads/{threadId}`               None                                                                           `{thread,messages,attachments}`          401, 404

  `POST /threads/{threadId}/read-state`   `{is_read:boolean}`                                                            `{updated:true}`                         401, 404

  `POST /threads/{threadId}/archive`      `{}`                                                                           `{archived:true}`                        401, 404, 409

  `GET /search`                           Query                                                                          `{items,next_cursor,query}`              401, 422
                                          `q,account_id,from,to,after,before,label,unread,has_attachment,limit,cursor`                                            

  `GET /drafts`                           Query `status?,limit?,cursor?`                                                 `{items,next_cursor}`                    401

  `POST /drafts`                          `{account_id,thread_id?,to,cc,bcc,subject,body}`                               `{draft}`                                401, 422

  `GET /drafts/{draftId}`                 None                                                                           `{draft}`                                401, 404

  `PATCH /drafts/{draftId}`               `{revision,to?,cc?,bcc?,subject?,body?}`                                       `{draft}`                                401, 404, 409,
                                                                                                                                                                  422

  `DELETE /drafts/{draftId}`              `{}`                                                                           `{deleted:true}`                         401, 404, 409
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 7.4.6 Agent conversation endpoints

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Method and path                                         Request                                        Success response                           Errors
  ------------------------------------------------------- ---------------------------------------------- ------------------------------------------ -----------------
  `GET /agent/conversations`                              Query `limit?,cursor?`                         `{items,next_cursor}`                      401

  `POST /agent/conversations`                             `{title?,context_scope?}`                      `{conversation}`                           401, 422

  `GET /agent/conversations/{conversationId}`             None                                           `{conversation,messages}`                  401, 404

  `DELETE /agent/conversations/{conversationId}`          `{}`                                           `{archived:true}`                          401, 404

  `POST /agent/conversations/{conversationId}/messages`   `{content,context,stream,client_message_id}`   SSE stream; non-stream mode returns        401, 404, 409,
                                                                                                         `{message}`                                422, 429, 503,
                                                                                                                                                    504

  `POST /agent/conversations/{conversationId}/retry`      `{message_id,attempt_id}`                      SSE stream                                 401, 404, 409,
                                                                                                                                                    429, 503

  `GET /agent/status`                                     None                                           `{provider,model,available,quota_state}`   401
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 7.4.7 Tasks and decisions endpoints

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Method and path                          Request                                                          Success response                       Errors
  ---------------------------------------- ---------------------------------------------------------------- -------------------------------------- -----------------
  `GET /tasks`                             Query `status?,limit?,cursor?`                                   `{items,next_cursor}`                  401

  `POST /tasks`                            `{conversation_id,goal,plan,authorization_mode,context_scope}`   `{task,steps}`                         401, 403, 409,
                                                                                                                                                   422

  `GET /tasks/{taskId}`                    None                                                             `{task,steps,latest_events,outputs}`   401, 404

  `GET /tasks/{taskId}/events`             Query `after_sequence?,limit?`                                   `{items,next_sequence}`                401, 404

  `POST /tasks/{taskId}/pause`             `{}`                                                             `{task}`                               401, 404, 409

  `POST /tasks/{taskId}/resume`            `{acknowledge_summary:boolean}`                                  `{task}`                               401, 404, 409

  `POST /tasks/{taskId}/takeover`          `{}`                                                             `{task,edit_lock}`                     401, 404, 409

  `POST /tasks/{taskId}/return-control`    `{resume_with_updated_context:boolean,change_summary?}`          `{task}`                               401, 404, 409

  `POST /tasks/{taskId}/terminate`         `{confirmation:true,reason?}`                                    `{task,side_effect_summary}`           401, 404, 409

  `POST /tasks/{taskId}/retry`             `{step_id?,confirm_retry:true}`                                  `{task,step}`                          401, 404, 409,
                                                                                                                                                   422

  `GET /decisions`                         Query `status?,task_id?`                                         `{items}`                              401

  `POST /decisions/{decisionId}/resolve`   `{choice,comment?,revision?}`                                    `{decision,task}`                      401, 404, 409,
                                                                                                                                                   422
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 7.4.8 Review Queue endpoints

  -----------------------------------------------------------------------------------------------------------------------------------------------
  Method and path                            Request                          Success response                                  Errors
  ------------------------------------------ -------------------------------- ------------------------------------------------- -----------------
  `GET /review`                              Query `status?,limit?,cursor?`   `{items,next_cursor}`                             401

  `GET /review/{reviewId}`                   None                             `{review_item,draft,source_context,agent_note}`   401, 404

  `PATCH /review/{reviewId}`                 `{revision,draft_changes}`       `{review_item,draft}`                             401, 404, 409,
                                                                                                                                422

  `POST /review/{reviewId}/approve`          `{revision,confirm_send:true}`   `{review_item,send_result}`                       401, 403, 404,
                                                                                                                                409, 422, 502,
                                                                                                                                504

  `POST /review/{reviewId}/reject`           `{reason?}`                      `{review_item,task}`                              401, 404, 409

  `POST /review/{reviewId}/return-to-task`   `{comment?}`                     `{review_item,task}`                              401, 404, 409
  -----------------------------------------------------------------------------------------------------------------------------------------------

### 7.4.9 Automations endpoints

  -----------------------------------------------------------------------------------------------------------------------------------------------
  Method and path                              Request                                                  Success response        Errors
  -------------------------------------------- -------------------------------------------------------- ----------------------- -----------------
  `GET /automations`                           Query `enabled?`                                         `{items}`               401

  `POST /automations`                          `{name,trigger,conditions,actions,authorization_mode}`   `{automation}`          401, 422

  `GET /automations/{automationId}`            None                                                     `{automation,runs}`     401, 404

  `PATCH /automations/{automationId}`          `{revision,name?,trigger?,conditions?,actions?}`         `{automation}`          401, 404, 409,
                                                                                                                                422

  `POST /automations/{automationId}/enable`    `{}`                                                     `{automation}`          401, 404, 409

  `POST /automations/{automationId}/disable`   `{}`                                                     `{automation}`          401, 404, 409

  `POST /automations/{automationId}/run`       `{}`                                                     `{run}`                 401, 404, 409,
                                                                                                                                429

  `GET /automations/{automationId}/runs`       Query `limit?,cursor?`                                   `{items,next_cursor}`   401, 404

  `DELETE /automations/{automationId}`         `{}`                                                     `{deleted:true}`        401, 404, 409
  -----------------------------------------------------------------------------------------------------------------------------------------------

### 7.4.10 Archive endpoints

  --------------------------------------------------------------------------------------------------------------------------------
  Method and path                       Request                                          Success response        Errors
  ------------------------------------- ------------------------------------------------ ----------------------- -----------------
  `GET /archive`                        Query                                            `{items,next_cursor}`   401, 422
                                        `q?,after?,before?,account_id?,limit?,cursor?`                           

  `POST /archive/{messageId}/restore`   `{destination:"inbox"}`                          `{restored:true}`       401, 404, 409
  --------------------------------------------------------------------------------------------------------------------------------

### 7.4.11 Settings and data endpoints

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Method and path                       Request                                                   Success response                                     Errors
  ------------------------------------- --------------------------------------------------------- ---------------------------------------------------- -----------------
  `GET /settings`                       None                                                      `{profile,appearance,agent,notifications,privacy}`   401

  `PATCH /settings`                     `{profile?,appearance?,agent?,notifications?,privacy?}`   `{settings}`                                         401, 409, 422

  `POST /settings/data-export`          `{format:"json"}`                                         `{export_job}`                                       401, 429

  `GET /settings/data-export/{jobId}`   None                                                      `{status,download_url?}`                             401, 404

  `POST /settings/delete-demo-data`     `{confirm:true}`                                          `{deleted_counts}`                                   401, 409

  `DELETE /settings/account`            `{password,confirmation_text:"DELETE"}`                   `{account_deleted:true}`                             401, 403, 409,
                                                                                                                                                       422
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 7.4.12 Contacts and to-dos endpoints

  ---------------------------------------------------------------------------------------------------------------------------
  Method and path                  Request                                          Success response        Errors
  -------------------------------- ------------------------------------------------ ----------------------- -----------------
  `GET /contacts`                  Query `q?,limit?,cursor?`                        `{items,next_cursor}`   401

  `POST /contacts`                 `{name,email,company?,notes?}`                   `{contact}`             401, 409, 422

  `PATCH /contacts/{contactId}`    `{name?,email?,company?,notes?}`                 `{contact}`             401, 404, 422

  `DELETE /contacts/{contactId}`   `{}`                                             `{deleted:true}`        401, 404

  `GET /todos`                     Query `status?,due_before?`                      `{items}`               401

  `POST /todos`                    `{title,description?,due_at?,source_task_id?}`   `{todo}`                401, 422

  `PATCH /todos/{todoId}`          `{title?,description?,due_at?,status?}`          `{todo}`                401, 404, 409,
                                                                                                            422

  `DELETE /todos/{todoId}`         `{}`                                             `{deleted:true}`        401, 404
  ---------------------------------------------------------------------------------------------------------------------------

## 7.5 WebSocket event catalogue

Endpoint: `GET /api/v1/ws` upgraded to WebSocket. Authenticate using the
secure session cookie. Do not put long-lived bearer tokens in the URL
query string.

Client-to-server events:

  -------------------------------------------------------------------------------------------------------------
  Event                   Payload                                                       Purpose
  ----------------------- ------------------------------------------------------------- -----------------------
  `client.hello`          `{last_event_id?,subscriptions?}`                             Initialize connection
                                                                                        and resume

  `client.subscribe`      `{channels:["tasks","sync","notifications"],resource_ids?}`   Subscribe to owned
                                                                                        resources

  `client.unsubscribe`    `{channels,resource_ids?}`                                    Remove subscriptions

  `client.ping`           `{timestamp}`                                                 Keep-alive

  `client.task.ack`       `{task_id,event_sequence}`                                    Acknowledge task event

  `client.sync.request`   `{account_id}`                                                Request current sync
                                                                                        status

  `client.task.watch`     `{task_id}`                                                   Watch a task owned by
                                                                                        the user

  `client.task.unwatch`   `{task_id}`                                                   Stop watching
  -------------------------------------------------------------------------------------------------------------

Server-to-client events:

  ----------------------------------------------------------------------------------------------------------
  Event                      Payload                                                 Purpose
  -------------------------- ------------------------------------------------------- -----------------------
  `server.hello`             `{connection_id,server_time,resume_from}`               Connection accepted

  `server.heartbeat`         `{timestamp}`                                           Keep-alive

  `server.error`             `{code,message,retryable}`                              Connection or
                                                                                     subscription error

  `notification.created`     `{notification_id,type,title,body,resource}`            In-app notification

  `sync.started`             `{job_id,account_id,environment,mode}`                  Sync began

  `sync.progress`            `{job_id,phase,processed,total,percent,simulated}`      Sync progress

  `sync.completed`           `{job_id,account_id,counts,completed_at,simulated}`     Sync finished

  `sync.failed`              `{job_id,error_code,message,retryable}`                 Sync failed

  `mail.new`                 `{account_id,thread_id,message_id,environment}`         New message available

  `mail.updated`             `{message_id,changed_fields}`                           Message changed

  `task.created`             `{task_id,status,goal}`                                 Task created

  `task.queued`              `{task_id,position}`                                    Task queued

  `task.started`             `{task_id,started_at}`                                  Task started

  `task.progress`            `{task_id,percent,summary,current_step_id}`             Overall progress

  `task.step.started`        `{task_id,step_id,sequence,title}`                      Step started

  `task.step.progress`       `{task_id,step_id,percent,summary}`                     Step progress

  `task.step.completed`      `{task_id,step_id,output_refs}`                         Step completed

  `task.step.failed`         `{task_id,step_id,error_code,message,retryable}`        Step failed

  `task.waiting_user`        `{task_id,reason,decision_id}`                          Task paused for user

  `task.decision.required`   `{task_id,decision_id,decision_type,summary,options}`   User decision needed

  `task.paused`              `{task_id,reason}`                                      Task paused

  `task.resumed`             `{task_id,resumed_at}`                                  Task resumed

  `task.takeover`            `{task_id,lock_owner:"user"}`                           User has control

  `task.terminated`          `{task_id,completed_steps,side_effects}`                Task terminated

  `task.completed`           `{task_id,completed_at,output_refs}`                    Task completed

  `task.failed`              `{task_id,error_code,message,recovery_options}`         Task failed

  `task.output.created`      `{task_id,output_type,output_id,review_id?}`            Output created

  `task.log.appended`        `{task_id,event_id,level,message,created_at}`           Timeline log

  `review.created`           `{review_id,task_id,draft_id,subject,recipient}`        New review item

  `review.updated`           `{review_id,status,revision}`                           Review changed

  `agent.status`             `{provider,model,available,quota_state}`                Model availability

  `session.expiring`         `{expires_at}`                                          Session warning

  `session.revoked`          `{reason}`                                              Session revoked
  ----------------------------------------------------------------------------------------------------------

Every server event must be scoped to the authenticated user and
authorized resources. Events are persisted or recoverable from REST
before being broadcast. A client must treat the event stream as an
update signal, not as the sole source of truth.

## 7.6 Database schema --- remaining application tables

Use UUID primary keys, foreign keys, indexes on ownership/status/time,
and `created_at` / `updated_at` timestamps where applicable. JSON
columns must be validated at the API boundary.

### `users`

-   `id UUID PRIMARY KEY`
-   `name TEXT NOT NULL`
-   `email TEXT UNIQUE NOT NULL`
-   `password_hash TEXT NOT NULL`
-   `status TEXT NOT NULL`
-   `terms_accepted_at TIMESTAMP`
-   `email_verified_at TIMESTAMP NULL`
-   `created_at TIMESTAMP NOT NULL`
-   `updated_at TIMESTAMP NOT NULL`
-   `deleted_at TIMESTAMP NULL`

### `sessions`

-   `id UUID PRIMARY KEY`
-   `user_id UUID REFERENCES users`
-   `session_hash TEXT UNIQUE NOT NULL`
-   `csrf_token_hash TEXT`
-   `ip_hash TEXT NULL`
-   `user_agent TEXT NULL`
-   `expires_at TIMESTAMP NOT NULL`
-   `last_seen_at TIMESTAMP NOT NULL`
-   `revoked_at TIMESTAMP NULL`
-   `created_at TIMESTAMP NOT NULL`

### `onboarding_states`

-   `id UUID PRIMARY KEY`
-   `user_id UUID UNIQUE REFERENCES users`
-   `state TEXT NOT NULL`
-   `completed_steps JSON NOT NULL`
-   `mailbox_choice TEXT NULL`
-   `last_error_code TEXT NULL`
-   `created_at TIMESTAMP`
-   `updated_at TIMESTAMP`

### `sync_jobs`

-   `id UUID PRIMARY KEY`
-   `user_id UUID`
-   `mail_account_id UUID`
-   `mode TEXT`
-   `environment TEXT`
-   `status TEXT`
-   `phase TEXT`
-   `processed_count INTEGER`
-   `total_count INTEGER NULL`
-   `cursor_before TEXT NULL`
-   `cursor_after TEXT NULL`
-   `error_code TEXT NULL`
-   `started_at TIMESTAMP NULL`
-   `completed_at TIMESTAMP NULL`
-   `created_at TIMESTAMP`

### `agent_conversations`

-   `id UUID PRIMARY KEY`
-   `user_id UUID`
-   `title TEXT`
-   `status TEXT`
-   `context_scope JSON`
-   `summary TEXT NULL`
-   `created_at TIMESTAMP`
-   `updated_at TIMESTAMP`
-   `last_message_at TIMESTAMP NULL`

### `agent_messages`

-   `id UUID PRIMARY KEY`
-   `conversation_id UUID`
-   `user_id UUID`
-   `role TEXT`
-   `content TEXT`
-   `content_json JSON NULL`
-   `model_provider TEXT NULL`
-   `model_id TEXT NULL`
-   `status TEXT`
-   `client_message_id TEXT NULL`
-   `attempt_id UUID NULL`
-   `input_tokens INTEGER NULL`
-   `output_tokens INTEGER NULL`
-   `error_code TEXT NULL`
-   `created_at TIMESTAMP`
-   `completed_at TIMESTAMP NULL`

### `tasks`

-   `id UUID PRIMARY KEY`
-   `user_id UUID`
-   `conversation_id UUID NULL`
-   `goal TEXT`
-   `status TEXT`
-   `authorization_mode TEXT`
-   `plan_json JSON`
-   `context_scope JSON`
-   `progress_percent INTEGER`
-   `current_step_id UUID NULL`
-   `execution_lock TEXT NULL`
-   `environment TEXT`
-   `error_code TEXT NULL`
-   `started_at TIMESTAMP NULL`
-   `completed_at TIMESTAMP NULL`
-   `created_at TIMESTAMP`
-   `updated_at TIMESTAMP`

### `task_steps`

-   `id UUID PRIMARY KEY`
-   `task_id UUID`
-   `sequence INTEGER`
-   `step_type TEXT`
-   `title TEXT`
-   `description TEXT`
-   `input_refs JSON`
-   `output_refs JSON`
-   `status TEXT`
-   `risk_level TEXT`
-   `requires_approval BOOLEAN`
-   `approval_id UUID NULL`
-   `progress_percent INTEGER`
-   `retry_count INTEGER`
-   `idempotency_key TEXT`
-   `error_code TEXT NULL`
-   `started_at TIMESTAMP NULL`
-   `completed_at TIMESTAMP NULL`
-   `created_at TIMESTAMP`

### `task_events`

-   `id UUID PRIMARY KEY`
-   `task_id UUID`
-   `user_id UUID`
-   `sequence BIGINT`
-   `event_type TEXT`
-   `payload JSON`
-   `created_at TIMESTAMP`
-   Unique index on `(task_id, sequence)`.

### `decisions`

-   `id UUID PRIMARY KEY`
-   `task_id UUID`
-   `step_id UUID NULL`
-   `user_id UUID`
-   `decision_type TEXT`
-   `prompt TEXT`
-   `options JSON`
-   `status TEXT`
-   `response JSON NULL`
-   `expires_at TIMESTAMP NULL`
-   `resolved_at TIMESTAMP NULL`
-   `created_at TIMESTAMP`

### `review_items`

-   `id UUID PRIMARY KEY`
-   `user_id UUID`
-   `task_id UUID`
-   `draft_id UUID`
-   `status TEXT`
-   `agent_note TEXT NULL`
-   `source_refs JSON`
-   `revision INTEGER`
-   `environment TEXT`
-   `approved_at TIMESTAMP NULL`
-   `rejected_at TIMESTAMP NULL`
-   `created_at TIMESTAMP`
-   `updated_at TIMESTAMP`

### `automations`

-   `id UUID PRIMARY KEY`
-   `user_id UUID`
-   `name TEXT`
-   `trigger JSON`
-   `conditions JSON`
-   `actions JSON`
-   `authorization_mode TEXT`
-   `enabled BOOLEAN`
-   `revision INTEGER`
-   `last_run_at TIMESTAMP NULL`
-   `next_run_at TIMESTAMP NULL`
-   `created_at TIMESTAMP`
-   `updated_at TIMESTAMP`

### `automation_runs`

-   `id UUID PRIMARY KEY`
-   `automation_id UUID`
-   `user_id UUID`
-   `status TEXT`
-   `trigger_payload JSON`
-   `result_payload JSON NULL`
-   `error_code TEXT NULL`
-   `started_at TIMESTAMP`
-   `completed_at TIMESTAMP NULL`

### `audit_logs`

-   `id UUID PRIMARY KEY`
-   `user_id UUID`
-   `actor_type TEXT`
-   `actor_id UUID NULL`
-   `action TEXT`
-   `resource_type TEXT`
-   `resource_id UUID NULL`
-   `environment TEXT`
-   `result TEXT`
-   `metadata JSON`
-   `ip_hash TEXT NULL`
-   `created_at TIMESTAMP`

Audit logs are append-only from the application layer. Never include API
keys, passwords, refresh tokens or full sensitive message bodies.

### `contacts`

-   `id UUID PRIMARY KEY`
-   `user_id UUID`
-   `name TEXT`
-   `email TEXT`
-   `company TEXT NULL`
-   `notes TEXT NULL`
-   `source TEXT`
-   `created_at TIMESTAMP`
-   `updated_at TIMESTAMP`

Unique constraint may apply to normalized `(user_id,email)`.

### `todos`

-   `id UUID PRIMARY KEY`
-   `user_id UUID`
-   `source_task_id UUID NULL`
-   `source_message_id UUID NULL`
-   `title TEXT`
-   `description TEXT NULL`
-   `due_at TIMESTAMP NULL`
-   `status TEXT`
-   `created_by TEXT`
-   `created_at TIMESTAMP`
-   `updated_at TIMESTAMP`
-   `completed_at TIMESTAMP NULL`

### `notifications`

-   `id UUID PRIMARY KEY`
-   `user_id UUID`
-   `type TEXT`
-   `title TEXT`
-   `body TEXT`
-   `resource_type TEXT NULL`
-   `resource_id UUID NULL`
-   `read_at TIMESTAMP NULL`
-   `created_at TIMESTAMP`

### `user_settings`

-   `id UUID PRIMARY KEY`
-   `user_id UUID UNIQUE`
-   `appearance TEXT`
-   `default_authorization_mode TEXT`
-   `agent_preferences JSON`
-   `notification_preferences JSON`
-   `privacy_preferences JSON`
-   `created_at TIMESTAMP`
-   `updated_at TIMESTAMP`

### `idempotency_records`

-   `id UUID PRIMARY KEY`
-   `user_id UUID`
-   `idempotency_key TEXT`
-   `operation TEXT`
-   `request_hash TEXT`
-   `response_json JSON`
-   `status TEXT`
-   `created_at TIMESTAMP`
-   `expires_at TIMESTAMP`
-   Unique constraint on `(user_id,idempotency_key,operation)`.

### `oauth_states`

-   `id UUID PRIMARY KEY`
-   `user_id UUID`
-   `provider TEXT`
-   `state_hash TEXT`
-   `pkce_verifier_ciphertext TEXT NULL`
-   `redirect_uri TEXT`
-   `expires_at TIMESTAMP`
-   `consumed_at TIMESTAMP NULL`
-   `created_at TIMESTAMP`

## 7.7 Account and session design

-   Email is the unique account identifier and is normalized to
    lowercase.
-   Passwords are hashed using Argon2id.
-   Sessions use opaque, cryptographically random tokens stored as
    secure, HttpOnly, SameSite cookies.
-   Store only a hash of the session token in the database.
-   Use `Secure` cookies in HTTPS deployment.
-   Rotate session identifiers after login and privilege-sensitive
    actions.
-   CSRF protection is required for cookie-authenticated mutation
    endpoints.
-   Session expiry: 7 days absolute, 24 hours idle for the demo default;
    configurable.
-   Logout revokes the current session.
-   Users can view and revoke other sessions.
-   OAuth provider tokens are encrypted at rest and never exposed to the
    frontend.
-   Demo sessions are visibly marked and may use shorter expiry.
-   Do not use a shared hard-coded demo password in public
    documentation.

## 7.8 Security and privacy requirements

1.  Enforce ownership checks on every user-scoped resource.
2.  Validate every state transition on the backend.
3.  Use CSRF protection for cookie-authenticated mutations.
4.  Apply rate limits to login, registration, password reset and Agent
    calls.
5.  Sanitize HTML email bodies before rendering.
6.  Escape user and email content; never render raw untrusted HTML.
7.  Restrict attachment size and MIME types; scan or block unsupported
    content.
8.  Encrypt provider tokens at rest using a server-side encryption key.
9.  Keep `GROQ_API_KEY`, OAuth secrets, session signing keys and
    encryption keys in environment variables.
10. Redact secrets from logs and exception traces.
11. Apply strict CORS to the same-origin deployed application; do not
    use wildcard origins with credentials.
12. Use HTTPS only in public deployment.
13. Use Content Security Policy and secure response headers.
14. Treat emails and attachments as untrusted prompt context.
15. Require explicit approval for sending and other consequential
    operations.
16. Audit account, mailbox, task, review and destructive actions.
17. Provide user-facing data export and account deletion.
18. Do not train models on mailbox content.
19. Do not claim legal/compliance certifications that have not been
    obtained.
20. Demo data must be synthetic and must not contain real personal
    information.

## 7.9 Environment variables

  ----------------------------------------------------------------------------------------
  Variable                      Required                Description
  ----------------------------- ----------------------- ----------------------------------
  `APP_ENV`                     Yes                     `development`, `demo` or
                                                        `production`

  `APP_BASE_URL`                Yes                     Public application origin

  `DATABASE_URL`                Yes                     SQLite path or PostgreSQL URL

  `SESSION_SECRET`              Yes                     High-entropy session/CSRF signing
                                                        secret

  `TOKEN_ENCRYPTION_KEY`        Yes for real OAuth      Key used to encrypt provider
                                                        tokens

  `GROQ_API_KEY`                Yes for live Agent      Groq API key; backend only

  `GROQ_BASE_URL`               No                      Defaults to
                                                        `https://api.groq.com/openai/v1`

  `GROQ_MODEL`                  No                      Defaults to `openai/gpt-oss-20b`

  `GOOGLE_CLIENT_ID`            Optional                Google OAuth client ID

  `GOOGLE_CLIENT_SECRET`        Optional                Google OAuth client secret

  `MICROSOFT_CLIENT_ID`         Optional                Microsoft OAuth client ID

  `MICROSOFT_CLIENT_SECRET`     Optional                Microsoft OAuth client secret

  `OAUTH_REDIRECT_BASE_URL`     Optional                Backend OAuth callback origin

  `DEMO_MODE_ENABLED`           Yes                     Enables Demo Mailbox

  `DEMO_SEED_PROFILE`           No                      Seed profile name

  `DEMO_SYNC_DELAY_MS`          No                      Simulated sync progress duration

  `AGENT_REQUESTS_PER_MINUTE`   No                      App-level rate limit

  `AGENT_REQUESTS_PER_DAY`      No                      App-level daily limit

  `LOG_LEVEL`                   No                      Logging verbosity

  `SENTRY_DSN`                  No                      Optional; omit if no free plan is
                                                        available or configured
  ----------------------------------------------------------------------------------------

Never commit `.env` files or secrets to source control.

## 7.10 Deployment steps --- one deployable web service

1.  Build the React frontend using Vite.
2.  Copy the frontend build output into the backend static directory.
3.  Configure FastAPI to serve `/api/v1/*`, `/api/v1/ws`, SSE and static
    frontend routes.
4.  Add database migrations and a startup health check.
5.  Add a deterministic seed command for Demo Mailbox.
6.  Configure Render as one web service with a Python build/start
    command.
7.  Set required environment variables in the host dashboard.
8.  Configure persistent disk only if supported by the chosen plan;
    otherwise label the demo database as ephemeral and reseed safely.
9.  Configure HTTPS and the exact OAuth callback URLs if real provider
    OAuth is enabled.
10. Deploy and wait for health check success.
11. Verify the public URL in a clean browser session.
12. Test registration, Demo Mailbox onboarding, Agent streaming, task
    WebSocket, review approval and theme persistence.
13. Publish the test URL only after the smoke test passes.
14. Display a warm-up state if the free host has slept and requires
    startup time.

The deployable application must remain useful if real OAuth credentials
are absent: the Demo Mailbox and Agent free-model integration are the
reviewer's default path. If the Groq key is absent or quota is
exhausted, use the exact Section 5 fallback and preserve manual
functionality.

## 7.11 Seed-data plan

Seed **30--50 synthetic messages** across 10--15 threads. All names,
organizations, domains and message bodies must be fictional and clearly
part of Demo Mailbox.

Suggested synthetic organizations and contacts:

-   Acme Studio --- quotation follow-up.
-   Northstar --- meeting coordination.
-   Orion Labs --- partnership terms.
-   Pine & Co --- invoice clarification.
-   Meridian Systems --- product questions.
-   Harbor Design --- delivery schedule.
-   Atlas Research --- document review.
-   Cedar Ventures --- introductory conversation.

Seed content should include:

-   30--50 messages.
-   10--15 threads.
-   8--12 senders/contacts.
-   5--8 messages with attachments (synthetic metadata or safe local
    sample files).
-   Read and unread messages.
-   Starred messages.
-   Inbox, Sent, Drafts, Archive and Trash examples.
-   A few overdue and upcoming action items.
-   Three active tasks with varied states.
-   Two or three pending Review Queue items.
-   Two automations, one enabled and one disabled.
-   Several completed task events and one recoverable failed step.
-   At least one sample prompt-injection email for testing the
    untrusted-content boundary; it must not contain real credentials or
    executable content.

### Consistent demo task data

Use stable IDs and maintain consistency across Briefing, Delegate Work,
Task Progress and Review Queue:

-   `AG-2048` --- Acme Studio quotation follow-up. Draft awaiting
    approval.
-   `AG-2051` --- Northstar meeting coordination. Waiting for user to
    choose a time.
-   `AG-2054` --- Orion Labs partnership terms. In progress; terms
    summary completed, clarification pending.

Seed IDs should remain stable across resets so automated acceptance
tests can reference them.

### Demo labelling

The shell, Inbox, sync status, task details, Review Queue and send
confirmations must identify Demo Mailbox activity. Use
`environment=demo` in all seeded records and all generated task outputs.
Never mix demo and live mailbox records in a single unlabelled list.

## 7.12 Interviewer experience path

A reviewer should be able to complete the following journey without
help:

1.  Open the public test URL.
2.  See the Intenda sign-in/create-account screen.
3.  Choose `Use the Demo Mailbox` or create a test account.
4.  Read the explicit Demo Mailbox notice: messages and sync are
    simulated; no external emails will be sent.
5.  Watch the simulated sync progress complete.
6.  Arrive at Today Briefing and see summary metrics, pending decisions
    and active tasks.
7.  Open Inbox and select the Acme Studio thread.
8.  Read the thread and click `Hand to Agent`.
9.  In Delegate Work, enter:
    `Draft a polite follow-up to Acme Studio asking whether they have reviewed the quotation and whether they need any changes.`
10. Confirm the selected thread is attached as context.
11. Review the Agent's generated plan and choose
    `Fully Automatic but Confirm Before Sending`.
12. Click `Start execution`.
13. Open Task Progress and observe step updates over WebSocket.
14. Wait for the draft output to appear in Review Queue.
15. Open the draft, inspect recipient, subject and body, and make an
    optional edit.
16. Click `Approve & Send`.
17. Read the confirmation that the operation is a simulated send and no
    external email will be delivered.
18. Confirm the simulated send.
19. Verify that the review item is marked approved/sent, the task is
    completed, the demo Sent folder contains the message, and the audit
    log records the operation.
20. Change Appearance from the bottom-left sidebar control and verify
    the selected mode persists after navigation and reload.

The happy path should take approximately 3--5 minutes after the service
is warm. If Groq is unavailable, the reviewer must still be able to
inspect the manual email workflow and see the exact fallback message;
the application must not fabricate successful Agent execution.

------------------------------------------------------------------------

# Section 8 --- Acceptance checklist

All P0 items below must pass before delivery. A partial implementation
must not be described as complete.

## 8.1 Application shell and navigation

-   [ ] Intenda branding is present and consistent.
-   [ ] Desktop reference layout is 1440 × 900.
-   [ ] Sidebar is 248px wide at the reference viewport.
-   [ ] Top bar is present and does not contain the appearance toggle.
-   [ ] All eight sidebar entries navigate to their correct pages.
-   [ ] Active route is visibly indicated.
-   [ ] Counts and notification badges reflect backend state.
-   [ ] No dead navigation entries or decorative-only buttons remain.
-   [ ] Responsive behaviour does not make core controls unreachable.

## 8.2 V4 visual system

-   [ ] Day mode uses black text, white/light-grey surfaces and neutral
    borders.
-   [ ] Night mode uses near-black, graphite and neutral-grey surfaces.
-   [ ] The only brand/action blue is `#2563EB`.
-   [ ] Primary buttons, selected states, notification dots and avatar
    backgrounds use the same `#2563EB`.
-   [ ] No purple, violet, indigo, neon or purple-blue gradient remains.
-   [ ] Khaki/macaron semantic accents are muted and small-area only.
-   [ ] Inter and Noto Sans SC load with appropriate system fallbacks.
-   [ ] Text contrast is usable in both modes.
-   [ ] Hover, focus, disabled and selected states are visible in both
    modes.

## 8.3 Appearance toggle

-   [ ] Appearance control is at the bottom-left of the sidebar.
-   [ ] It includes an icon, the label `Appearance` and current-state
    text `Day` or `Night`.
-   [ ] It opens a two-option Day/Night menu.
-   [ ] Selecting a mode changes the entire application without reload.
-   [ ] Preference persists across route changes and browser reload.
-   [ ] Server preference and local fallback are reconciled correctly.
-   [ ] Keyboard operation works with Enter, Space, arrows, Escape and
    Tab.
-   [ ] Accessible name, menu state and selected radio state are
    exposed.
-   [ ] The toggle is completely absent from the top bar.
-   [ ] Theme change does not alter layout or lose unsaved user input.

## 8.4 Eight fully working pages

### Today Briefing

-   [ ] Metrics load from the briefing API.
-   [ ] Decision cards link to the correct Review Queue item.
-   [ ] Task cards link to the correct Task Progress detail.
-   [ ] Recent messages open the correct Inbox thread.
-   [ ] Empty, loading and error states work.
-   [ ] Every visible action produces a real navigation or mutation.

### Delegate Work

-   [ ] User can enter a natural-language goal.
-   [ ] User can attach and remove email context.
-   [ ] Agent plan streams into the page.
-   [ ] Authorization mode is required before execution.
-   [ ] Start execution creates exactly one task.
-   [ ] Failed model response preserves the user's input and creates no
    task.
-   [ ] Empty, loading and error states work.

### Task Progress

-   [ ] Task list and task detail load.
-   [ ] Timeline shows persisted events in order.
-   [ ] WebSocket updates progress in real time.
-   [ ] Reconnect recovers missed events.
-   [ ] Pause, resume, takeover and terminate enforce backend state
    rules.
-   [ ] Completed work remains visible after pause or termination.
-   [ ] Draft outputs link to Review Queue.
-   [ ] Empty, loading and error states work.

### Inbox

-   [ ] Folder navigation works.
-   [ ] Message/thread list and reading pane load.
-   [ ] Search supports query and filters.
-   [ ] Compose, save draft, reply, reply all and forward work.
-   [ ] Mark read/unread and star/unstar work.
-   [ ] Archive and delete work.
-   [ ] Hand to Agent attaches the selected thread.
-   [ ] Send failure preserves the draft.
-   [ ] Demo send is clearly labelled simulated.
-   [ ] Empty, loading and error states work.

### Review Queue

-   [ ] Review items load and filters work.
-   [ ] Full draft content and source context are visible.
-   [ ] Draft can be edited and saved with revision control.
-   [ ] Approve & Send requires confirmation.
-   [ ] Reject and Return to Task work.
-   [ ] Failed send leaves the draft recoverable.
-   [ ] Demo and live sends are distinguished.
-   [ ] Empty, loading and error states work.

### Automations

-   [ ] User can create, edit, enable, disable, run and delete an
    automation.
-   [ ] Trigger and condition validation works.
-   [ ] Run history is persisted.
-   [ ] Automation cannot bypass Review Queue send approval.
-   [ ] Failed runs show actionable errors.
-   [ ] Empty, loading and error states work.

### Archive

-   [ ] Archived messages load and can be searched.
-   [ ] Restore returns a message to Inbox.
-   [ ] Delete moves a message to Trash/soft-deleted state.
-   [ ] Hand to Agent works from archived context.
-   [ ] Empty, loading and error states work.

### Settings

-   [ ] Profile settings load and save.
-   [ ] Mailbox connection status is visible.
-   [ ] Connect, reconnect and disconnect controls work or show a clear
    configuration-disabled state.
-   [ ] Agent preferences load and save.
-   [ ] Appearance preference is shown and consistent with the sidebar
    toggle.
-   [ ] Notification settings persist.
-   [ ] Session revocation works.
-   [ ] Data export and account deletion flows have confirmations and
    accurate outcomes.
-   [ ] Empty, loading and error states work.

## 8.5 Registration and onboarding

-   [ ] New user can register.
-   [ ] Password is stored as an Argon2id hash.
-   [ ] Login and logout work.
-   [ ] Duplicate registration is handled safely.
-   [ ] User can choose a real provider or Demo Mailbox.
-   [ ] Authorization explanation is shown before OAuth redirect.
-   [ ] OAuth state and callback validation work when credentials are
    configured.
-   [ ] OAuth cancellation and failure allow retry or Demo Mailbox.
-   [ ] Demo Mailbox creation is deterministic and labelled.
-   [ ] Sync progress updates in real time.
-   [ ] Sync failure can be retried.
-   [ ] Refreshing onboarding resumes at the correct state.
-   [ ] Successful onboarding enters Today Briefing.

## 8.6 Email capability and sync

-   [ ] List, read, search, compose, reply, reply all and forward work.
-   [ ] Draft autosave and revision conflict handling work.
-   [ ] Archive, Trash and restore work.
-   [ ] Attachments display safe metadata and download only when
    permitted.
-   [ ] Hand to Agent transfers only selected context.
-   [ ] Demo sync is simulated and labelled.
-   [ ] Real provider sync uses server-side OAuth tokens.
-   [ ] Demo sends never call a real provider.
-   [ ] Live sends show the actual provider result.
-   [ ] Send idempotency prevents duplicate sends on retry.
-   [ ] Provider throttling and reauthorization states are handled.
-   [ ] No cross-user mailbox access is possible.

## 8.7 Agent model integration

-   [ ] Backend calls Groq through the OpenAI-compatible API.
-   [ ] Default model ID is `openai/gpt-oss-20b`.
-   [ ] `GROQ_API_KEY` exists only in backend environment.
-   [ ] Browser network inspection reveals no provider key.
-   [ ] Responses stream incrementally through SSE.
-   [ ] Conversation and message records persist.
-   [ ] Timeouts, retries and rate limits are enforced.
-   [ ] Provider `429`, `5xx`, timeout and missing-key cases are
    handled.
-   [ ] Exact fallback wording is displayed when unavailable: "I'm
    temporarily unable to reach the AI model. Your request has been
    saved, but I have not taken any action. Please retry in a moment or
    continue manually."
-   [ ] A failed model request does not create a task, draft or external
    side effect.
-   [ ] Agent reads only selected/authorized context.
-   [ ] Prompt-injection test content cannot override system policy.
-   [ ] Agent cannot send, delete or change account settings without the
    required explicit user action.
-   [ ] No paid model or paid service is configured as fallback.

## 8.8 Delegation and task system

-   [ ] User goal generates an inspectable plan.
-   [ ] Task starts only after explicit user confirmation.
-   [ ] All three authorization modes are selectable and enforced
    server-side.
-   [ ] Confirm Every Step pauses before every step.
-   [ ] Confirm at Key Milestones pauses at defined milestones.
-   [ ] Fully Automatic but Confirm Before Sending runs safe internal
    steps but stops before every send.
-   [ ] Task lifecycle transitions are validated.
-   [ ] WebSocket task progress updates in real time.
-   [ ] Event sequence supports reconnect/replay.
-   [ ] Pause prevents new steps.
-   [ ] Resume continues from the next safe step.
-   [ ] Take Over locks Agent execution and preserves manual edits.
-   [ ] Terminate prevents future steps and records completed side
    effects.
-   [ ] Outputs appear in Review Queue.
-   [ ] Retry does not duplicate non-idempotent external operations.

## 8.9 API, database and deployment

-   [ ] All documented REST endpoints are implemented or explicitly
    return a documented feature-disabled response.
-   [ ] Request/response schemas are validated.
-   [ ] Ownership checks apply to every resource.
-   [ ] Standard error envelope and status codes are consistent.
-   [ ] WebSocket event catalogue is implemented for supported features.
-   [ ] Events are persisted or recoverable after reconnect.
-   [ ] Database migrations run from a clean database.
-   [ ] SQLite demo mode works.
-   [ ] PostgreSQL-compatible types and constraints are maintained.
-   [ ] Seed command creates 30--50 synthetic messages and all linked
    demo objects.
-   [ ] Stable demo task IDs AG-2048, AG-2051 and AG-2054 are present.
-   [ ] One deployable web service serves frontend and backend.
-   [ ] Public test URL is verified in a clean browser session before
    delivery.
-   [ ] Free-host sleep/restart behaviour is explained accurately.
-   [ ] No paid purchase, subscription or service is required for the
    demo path.

## 8.10 Security and quality

-   [ ] HTTPS is enforced on public deployment.
-   [ ] Session cookies are HttpOnly, Secure and SameSite.
-   [ ] CSRF protection is enabled for cookie-authenticated mutations.
-   [ ] Passwords use Argon2id.
-   [ ] OAuth tokens are encrypted at rest.
-   [ ] API keys and secrets are not committed or logged.
-   [ ] Email HTML is sanitized.
-   [ ] Attachments are size/type constrained.
-   [ ] Prompt-injection boundaries are tested.
-   [ ] Audit logs capture consequential actions without secrets or full
    sensitive bodies.
-   [ ] Account deletion and data export behave as documented.
-   [ ] Automated tests cover auth, onboarding, email, Agent fallback,
    task transitions and review approval.
-   [ ] End-to-end smoke test covers the full interviewer path.
-   [ ] No visible button is inert.
-   [ ] No user action is reported successful before backend
    confirmation.

## 8.11 Delivery summary

V1.0 is ready for review only when all P0 checklist items pass. The
reviewer must be able to enter through a public test link, use the Demo
Mailbox without connecting a personal account, see a genuine
Groq-powered Agent response when the free model is available, delegate a
task, watch real-time progress, review and approve a draft, and switch
Day/Night mode from the bottom-left sidebar control.

The product must remain useful when the free model or provider is
unavailable: manual email capabilities continue to work, the exact
fallback message is shown, and no action is fabricated or silently
executed. Demo activity is always labelled as simulated. No paid model,
purchase, subscription or paid service is required for the v1.0 demo
path.

**End of Intenda Product Specification v1.0.**
