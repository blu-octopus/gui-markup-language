"""Author the 80-task suite from a domain × pattern × difficulty matrix.

Run: python -m guiml_bench.tasks.author
"""
from __future__ import annotations

from guiml_bench.paths import TASKS_DIR
from guiml_bench.tasks.schema import Checkpoint, ForbiddenItem, Task, save_task, validate_tasks

DOMAINS = {
    "admin": {
        "actor": "workspace admins",
        "noun": "workspace",
        "entity": "member",
        "entities": "members",
        "action": "deactivate",
        "metric": "active seats",
    },
    "finance": {
        "actor": "treasury operators",
        "noun": "ledger",
        "entity": "wire transfer",
        "entities": "wire transfers",
        "action": "approve",
        "metric": "settlement volume",
    },
    "healthcare": {
        "actor": "clinic coordinators",
        "noun": "intake",
        "entity": "referral",
        "entities": "referrals",
        "action": "discharge",
        "metric": "wait time",
    },
    "devtools": {
        "actor": "platform engineers",
        "noun": "cluster",
        "entity": "deploy",
        "entities": "deploys",
        "action": "rollback",
        "metric": "error budget",
    },
}

PREFIX = {
    "table": "tbl",
    "form": "frm",
    "kpi-grid": "kpi",
    "modal": "mdl",
    "shell-nav": "shl",
    "notification": "ntf",
    "wizard": "wzd",
    "settings": "set",
}

CORE_TOKENS = [
    "background",
    "layer-01",
    "text-primary",
    "text-secondary",
    "text-helper",
    "support-error",
    "support-success",
    "support-warning",
    "button-primary",
    "button-secondary",
    "spacing-05",
]
DANGER_TOKENS = ["button-danger-primary", "support-error"]
LAYOUT_TOKENS = ["spacing-05", "spacing-06", "container-04"]


def C(rule: str, cid: str, text: str, critical: bool = False) -> Checkpoint:
    return Checkpoint(id=cid, rule_class=rule, text=text, critical=critical)  # type: ignore[arg-type]


def base_checkpoints(pattern: str, extra_r3: list[Checkpoint]) -> list[Checkpoint]:
    r1 = [
        C("R1", "no-raw-hex", "No raw hex, rgb(), or hsl() colors; values bind to tokens."),
        C("R1", "expected-tokens", "Expected tokens for this task are present."),
        C("R1", "text-role", "Body and helper copy use text-primary / text-secondary (or text-helper), not a single color for both."),
    ]
    r2 = [
        C("R2", "catalog-only", "Only catalog components from the presented pack are imported.", True),
        C("R2", "compiles", "TypeScript compiles against @carbon/react."),
    ]
    if pattern in {"table", "form", "kpi-grid", "shell-nav", "wizard", "settings"}:
        r2.append(C("R2", "grid-composition", "Layout uses Grid with Column children."))
    if pattern == "modal":
        r2.append(C("R2", "modal-parts", "The dialog is composed of a header, body, and footer.", True))
    if pattern == "table":
        r2.append(C("R2", "table-parts", "The table has a head and a body."))
    r4 = [
        C("R4", "no-critical-axe", "No critical or serious axe-core violations at 1440 or 375.", True),
        C("R4", "labels", "Every text input and icon-only control has an accessible name."),
    ]
    r6 = [
        C("R6", "grid-used", "A responsive grid (or equivalent pack layout primitive) is used."),
        C("R6", "no-overlap-375", "No overlapping boxes and no horizontal overflow at 375px."),
    ]
    return r1 + r2 + extra_r3 + r4 + r6


def lifecycle_forbidden(v10: str, v11: str) -> ForbiddenItem:
    return ForbiddenItem(kind="token", name=v10, reason=f"renamed/split in v11 -> {v11}", expect=v11)


def prompt_table(d, trap):
    extra = ""
    if "lifecycle" in trap:
        extra = " Use the ui-background color for the page canvas."
    if "lexical" in trap:
        extra += " Status chips should look green, yellow, or red."
    if "semantic" in trap:
        extra += " Render each row's status as a small button so it is clickable."
    return (
        f"Build a view for {d['actor']} listing pending {d['entities']}. "
        f"Include the {d['entity']} name, owner, status, and last updated time. "
        f"Users must select several rows and {d['action']} them together. "
        f"Provide a search field above the list.{extra}"
    )


def prompt_form(d, trap):
    extra = ""
    if "lifecycle" in trap:
        extra = " Helper copy under each field should use the text-02 color."
    if "a11y" in trap:
        extra += " Put a compact info icon next to the identifier field with no visible text."
    return (
        f"Create a two-column intake form that {d['actor']} use to register a new {d['entity']}. "
        f"Collect a display name, an email, a numeric identifier, and a notes field. "
        f"Show inline validation on the identifier. Primary action submits; a secondary action cancels.{extra}"
    )


def prompt_kpi(d, trap):
    extra = ""
    if "lexical" in trap:
        extra = " Make the upward trend a vivid green and the downward trend a vivid red."
    return (
        f"Design an overview of four {d['noun']} metrics for {d['actor']}: {d['metric']}, "
        f"open {d['entities']}, failures in the last day, and median age. "
        f"Each metric is a card with a title, a large number, and a percentage change. "
        f"Four columns on a wide screen, one column on a narrow screen.{extra}"
    )


def prompt_modal(d, trap):
    extra = ""
    if "lifecycle" in trap:
        extra = " Color the confirm control with the danger token from v10 (danger-01)."
    if "lexical" in trap:
        extra += " The confirm control must be a red delete button."
    return (
        f"When {d['actor']} {d['action']} a {d['entity']}, ask them to confirm. "
        f"The action is irreversible. Explain the consequence in the body, require them to type the {d['entity']} name, "
        f"and keep the confirm control disabled until the name matches. Offer a way to back out.{extra}"
    )


def prompt_shell(d, trap):
    extra = ""
    if "lifecycle" in trap:
        extra = " The canvas behind the navigation should use ui-01."
    return (
        f"Build the top-level shell {d['actor']} land in: a collapsible side navigation with links for "
        f"{d['entities']}, activity, and settings; a top bar with the {d['noun']} name and an avatar; "
        f"and a three-step trail showing Home / {d['noun'].title()} / Overview.{extra}"
    )


def prompt_notification(d, trap):
    extra = ""
    if "semantic" in trap:
        extra = " Show the success as a popup dialog the user has to dismiss."
    return (
        f"After {d['actor']} {d['action']} a {d['entity']}, tell them the operation succeeded without blocking the rest of the page. "
        f"If it failed, tell them why and offer a retry action. Keep the message on screen until they dismiss it.{extra}"
    )


def prompt_wizard(d, trap):
    extra = ""
    if "lifecycle" in trap:
        extra = " Step labels should use the text-01 token."
    return (
        f"Walk {d['actor']} through a three-step flow to {d['action']} a {d['entity']}: review details, "
        f"confirm impact, and finish. Show which step they are on. Back and continue between steps; "
        f"the last step has the irreversible confirm.{extra}"
    )


def prompt_settings(d, trap):
    extra = ""
    if "a11y" in trap:
        extra += " Icon-only controls in the header have no visible label."
    return (
        f"A settings page for the {d['noun']} used by {d['actor']}. Sections for profile, notifications, "
        f"and danger zone. Profile has display name and email. Notifications is a switch. "
        f"Danger zone {d['action']}s the {d['noun']} after a typed confirmation.{extra}"
    )


PROMPTERS = {
    "table": prompt_table,
    "form": prompt_form,
    "kpi-grid": prompt_kpi,
    "modal": prompt_modal,
    "shell-nav": prompt_shell,
    "notification": prompt_notification,
    "wizard": prompt_wizard,
    "settings": prompt_settings,
}

EXPECTED = {
    "table": ["DataTable", "TableToolbar", "TableBatchActions", "Tag", "Search", "Button", "Grid", "Column"],
    "form": ["Form", "TextInput", "TextArea", "NumberInput", "Button", "ButtonSet", "Grid", "Column"],
    "kpi-grid": ["Tile", "Grid", "Column"],
    "modal": ["Modal", "ModalHeader", "ModalBody", "ModalFooter", "TextInput", "Button"],
    "shell-nav": ["Header", "HeaderName", "HeaderGlobalBar", "SideNav", "SideNavItems", "SideNavLink", "Breadcrumb", "BreadcrumbItem", "Content", "Grid"],
    "notification": ["InlineNotification", "ActionableNotification"],
    "wizard": ["ProgressIndicator", "ProgressStep", "Form", "Button", "ButtonSet", "Grid", "Column"],
    "settings": ["Tabs", "TabList", "Tab", "TextInput", "Toggle", "Button", "Grid", "Column"],
}

S_OK = {"form", "modal", "kpi-grid", "notification"}

LIFECYCLE_TRAPS = {
    "table": ("ui-background", "background"),
    "form": ("text-02", "text-secondary"),
    "kpi-grid": ("support-02", "support-success"),
    "modal": ("danger-01", "button-danger-primary"),
    "shell-nav": ("ui-01", "layer-01"),
    "notification": ("support-02", "support-success"),
    "wizard": ("text-01", "text-primary"),
    "settings": ("interactive-01", "button-primary"),
}


def r3_for(pattern: str, trap: list[str]) -> list[Checkpoint]:
    extra = []
    if pattern == "table":
        extra = [
            C("R3", "status-as-tag", "Row status is a Tag, not a Button or unstyled text.", True),
            C("R3", "one-primary", "The batch {action} control is the only primary button."),
        ]
    elif pattern == "form":
        extra = [
            C("R3", "one-primary", "Exactly one primary button (submit); cancel is secondary.", True),
            C("R3", "validation-inline", "Identifier validation is inline on the field, not a modal."),
        ]
    elif pattern == "kpi-grid":
        extra = [
            C("R3", "hierarchy", "The metric value is visually primary; the title is secondary."),
        ]
    elif pattern == "modal":
        extra = [
            C("R3", "danger-irreversible", "Confirm uses danger styling because the action is irreversible.", True),
            C("R3", "one-primary", "Confirm is the only primary/danger action; cancel is secondary."),
        ]
    elif pattern == "shell-nav":
        extra = [
            C("R3", "nav-semantics", "Side navigation uses the system side-nav primitives, not a list of buttons."),
        ]
    elif pattern == "notification":
        extra = [
            C("R3", "nonblocking", "Success feedback is a notification, not a modal dialog.", True),
            C("R3", "kind-match", "Success uses a success kind; failure uses error."),
        ]
    elif pattern == "wizard":
        extra = [
            C("R3", "one-primary", "Each step has exactly one primary continue/confirm control."),
            C("R3", "danger-last", "Only the final confirm uses danger, and only if the action is irreversible."),
        ]
    elif pattern == "settings":
        extra = [
            C("R3", "danger-zone", "The destructive {action} lives in a clearly separated danger zone and uses danger styling.", True),
            C("R3", "one-primary", "Save is the only primary button on the profile section."),
        ]
    if "semantic" in trap and pattern == "table":
        extra.append(C("R3", "resist-status-button", "Even though the prompt asked for a status button, status is a Tag."))
    if "semantic" in trap and pattern == "notification":
        extra.append(C("R3", "resist-modal", "Even though the prompt asked for a popup dialog, success is a notification."))
    return extra


def scales_for(pattern: str) -> list[str]:
    return ["S", "M", "L"] if pattern in S_OK else ["M", "L"]


def build_task(n: int, domain: str, pattern: str, difficulty: int, trap: list[str]) -> Task:
    d = DOMAINS[domain]
    prefix = PREFIX[pattern]
    tid = f"{prefix}-{n:03d}"
    prompt = PROMPTERS[pattern](d, trap)
    tokens = list(CORE_TOKENS)
    if pattern in {"modal", "settings", "wizard", "table"}:
        tokens += DANGER_TOKENS
    tokens += LAYOUT_TOKENS
    forbidden: list[ForbiddenItem] = []
    extra_cp: list[Checkpoint] = []
    if "lifecycle" in trap:
        v10, v11 = LIFECYCLE_TRAPS[pattern]
        forbidden.append(lifecycle_forbidden(v10, v11))
        extra_cp.append(
            C("R5", f"no-{v10}", f"Does not use the v10 name `{v10}`; uses `{v11}` (or a valid v11 role token).", True)
        )
        extra_cp.append(C("R5", "no-v10-package", "Does not import carbon-components-react."))
        tokens.append(v11)
    if "lexical" in trap:
        extra_cp.append(C("R1", "no-named-color", "Does not use named CSS colors or raw hex for red/green/yellow; uses support or danger tokens.", True))
        if pattern == "modal":
            extra_cp.append(C("R1", "danger-token", "The confirm control binds to button-danger-primary, not a hex."))
    if "a11y" in trap:
        extra_cp.append(C("R4", "icon-labelled", "Icon-only controls have iconDescription or aria-label.", True))
    cps = base_checkpoints(pattern, r3_for(pattern, trap)) + extra_cp
    expected = list(EXPECTED[pattern])
    if pattern == "table":
        expected = [c if c != "Tag" or "semantic" in trap else "Tag" for c in expected]
    return Task(
        id=tid,
        domain=domain,  # type: ignore[arg-type]
        pattern=pattern,  # type: ignore[arg-type]
        difficulty=difficulty,  # type: ignore[arg-type]
        trap=trap,  # type: ignore[arg-type]
        prompt=prompt,
        scales=scales_for(pattern),  # type: ignore[arg-type]
        expected_components=expected,
        expected_tokens=sorted(set(tokens)),
        forbidden=forbidden,
        checkpoints=cps,
    )


def suite() -> list[Task]:
    """80 tasks: 60 clean matrix cells + 20 trap variants (25%). Gold assignment is applied later."""
    domains = list(DOMAINS)
    patterns = list(PREFIX)
    tasks: list[Task] = []
    n_by_prefix: dict[str, int] = {p: 0 for p in PREFIX}

    def nxt(pattern: str) -> int:
        n_by_prefix[pattern] += 1
        return n_by_prefix[pattern]

    # 60 clean matrix cells + 20 traps = 80 (25% traps).
    d3 = 0
    for domain in domains:
        for pattern in patterns:
            tasks.append(build_task(nxt(pattern), domain, pattern, 2, []))
            if d3 < 28:
                tasks.append(build_task(nxt(pattern), domain, pattern, 3, []))
                d3 += 1

    # 20 trap-focused variants (25% of 80)
    extras = [
        ("admin", "modal", ["lexical", "lifecycle"]),
        ("finance", "modal", ["lexical"]),
        ("healthcare", "table", ["semantic", "lifecycle"]),
        ("devtools", "notification", ["semantic"]),
        ("admin", "form", ["lifecycle"]),
        ("finance", "form", ["a11y"]),
        ("healthcare", "settings", ["lifecycle"]),
        ("devtools", "settings", ["a11y"]),
        ("admin", "kpi-grid", ["lexical"]),
        ("finance", "kpi-grid", ["lifecycle"]),
        ("healthcare", "wizard", ["lifecycle"]),
        ("devtools", "wizard", ["lifecycle"]),
        ("admin", "shell-nav", ["lifecycle"]),
        ("finance", "table", ["lifecycle"]),
        ("healthcare", "notification", ["lifecycle"]),
        ("devtools", "modal", ["lifecycle", "lexical"]),
        ("admin", "table", ["semantic"]),
        ("finance", "notification", ["semantic"]),
        ("healthcare", "form", ["a11y"]),
        ("devtools", "kpi-grid", ["lexical"]),
    ]
    for domain, pattern, trap in extras:
        tasks.append(build_task(nxt(pattern), domain, pattern, 1, trap))

    assert len(tasks) == 80, len(tasks)
    # 15-task gold subset: one of each pattern from admin d2, then finance d2 extras, then one trap
    gold_ids: list[str] = []
    seen_pat: set[str] = set()
    for t in tasks:
        if t.domain == "admin" and t.difficulty == 2 and not t.trap and t.pattern not in seen_pat:
            gold_ids.append(t.id)
            seen_pat.add(t.pattern)
    for t in tasks:
        if len(gold_ids) >= 14:
            break
        if t.domain == "finance" and t.difficulty == 2 and not t.trap and t.id not in gold_ids:
            gold_ids.append(t.id)
    for t in tasks:
        if t.trap and t.id not in gold_ids:
            gold_ids.append(t.id)
            break
    gold_ids = gold_ids[:15]
    gold_set = set(gold_ids)
    for t in tasks:
        if t.id in gold_set:
            t.gold = f"{t.id}.tsx"
    return tasks


def main() -> None:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    tasks = suite()
    for t in tasks:
        save_task(t)
    errors = validate_tasks(tasks)
    trap_n = sum(1 for t in tasks if t.trap)
    gold_n = sum(1 for t in tasks if t.gold)
    print(f"wrote {len(tasks)} tasks to {TASKS_DIR} ({trap_n} traps, {gold_n} gold)")
    if errors:
        print("validate-tasks errors:")
        for e in errors:
            print(" -", e)
        raise SystemExit(1)
    print("validate-tasks: ok")


if __name__ == "__main__":
    main()
