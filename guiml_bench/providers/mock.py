"""Deterministic mock provider for tests, smoke, and CI without API keys.

Behavior is condition-aware: it reads a hint from the last system message
(`CONDITION=B0|B1|...`) and emits TSX that systematically violates the
classes that hypothesis H1 says that condition should fail, so the stats
pipeline has a signal even before a paid run.
"""
from __future__ import annotations

import time

from .base import Message, Usage

CLEAN = '''import React from 'react';
import { Grid, Column, Button, Tag, Form, TextInput, InlineNotification } from '@carbon/react';

export default function TaskView() {
  return (
    <Grid>
      <Column lg={16} md={8} sm={4}>
        <Form>
          <TextInput id="name" labelText="Name" helperText="Shown to others" />
          <Tag type="green">open</Tag>
          <InlineNotification kind="success" title="Saved" subtitle="You can keep working." />
          <Button kind="primary">Save</Button>
        </Form>
      </Column>
    </Grid>
  );
}
'''

VIBE = '''import React from 'react';

export default function TaskView() {
  return (
    <div style={{background:'#0f62fe', padding:'13px', color:'#fff'}}>
      <button style={{background:'red'}}>Delete</button>
      <button>Status: open</button>
      <div className="modal">Saved! Click OK.</div>
    </div>
  );
}
'''

PROSE_DRIFT = '''import React from 'react';
import { Button, TextInput } from '@carbon/react';

export default function TaskView() {
  return (
    <div style={{ background: '#f4f4f4', padding: '16px' }}>
      <TextInput id="n" labelText="Name" />
      <button className="status">open</button>
      <Button kind="primary">Save</Button>
      <Button kind="primary">Also save</Button>
    </div>
  );
}
'''

DUMP_OK_LEX = '''import React from 'react';
import { Grid, Column, Button, TextInput } from '@carbon/react';

export default function TaskView() {
  return (
    <Grid>
      <Column lg={16}>
        <div style={{ background: 'var(--cds-ui-background)', color: 'var(--cds-text-01)' }}>
          <TextInput id="n" labelText="Name" />
          <Button kind="primary">Save</Button>
          <Button>open</Button>
        </div>
      </Column>
    </Grid>
  );
}
'''

REGISTRY = '''import React from 'react';
import { Grid, Column, Button, Tag, TextInput, InlineNotification } from '@carbon/react';

export default function TaskView() {
  return (
    <Grid>
      <Column lg={16} md={8} sm={4}>
        <TextInput id="n" labelText="Name" helperText="Shown to others" />
        <Tag type="green">open</Tag>
        <Button kind="primary">Save</Button>
        <div className="popup">Saved successfully</div>
      </Column>
    </Grid>
  );
}
'''

GUIML_CLEAN = CLEAN

BY_HINT = {
    "B0": VIBE,
    "B1": PROSE_DRIFT,
    "B2": DUMP_OK_LEX,
    "B3": REGISTRY,
    "T": GUIML_CLEAN,
    "T-lint": DUMP_OK_LEX,
    "T-life": DUMP_OK_LEX,
    "T+MoE": GUIML_CLEAN,
}


class MockProvider:
    name = "mock"
    model = "mock-v1"

    def complete(self, messages, *, tools=None, json_mode=False, temperature=0.2, max_tokens=4096):
        t0 = time.time()
        blob = "\n".join(m.content for m in messages)
        hint = "B0"
        for key in BY_HINT:
            if f"CONDITION={key}" in blob:
                hint = key
                break
        if json_mode:
            text = '{"checkpoints": [{"id": "one-primary", "pass": true, "rationale": "mock"}]}'
        elif tools:
            text = ""
            calls = [{"name": tools[0]["name"], "arguments": {"query": "Button"}}]
            usage = Usage(input_tokens=len(blob) // 4, output_tokens=16, cost_usd=0.0, latency_s=time.time() - t0)
            return text, usage, calls
        else:
            text = BY_HINT.get(hint, VIBE)
        usage = Usage(input_tokens=len(blob) // 4, output_tokens=len(text) // 4, cost_usd=0.0, latency_s=time.time() - t0)
        return text, usage, []
