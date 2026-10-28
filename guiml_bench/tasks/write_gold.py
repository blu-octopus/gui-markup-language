"""Write gold @carbon/react files for the 15-task validation subset."""
from __future__ import annotations

from pathlib import Path

from guiml_bench.paths import GOLD_DIR
from guiml_bench.tasks.schema import load_tasks

HEADER = '''import React, { useMemo, useState } from 'react';
import {
  Accordion, AccordionItem,
  ActionableNotification,
  Breadcrumb, BreadcrumbItem,
  Button, ButtonSet,
  Column, Content,
  DataTable, Table, TableHead, TableRow, TableHeader, TableBody, TableCell,
  TableContainer, TableToolbar, TableToolbarContent, TableToolbarSearch,
  TableBatchActions, TableBatchAction, TableSelectAll, TableSelectRow,
  Dropdown,
  Form, FormGroup,
  Grid,
  Header, HeaderName, HeaderGlobalBar, HeaderMenuButton,
  InlineNotification,
  Modal, ModalHeader, ModalBody, ModalFooter,
  NumberInput,
  ProgressIndicator, ProgressStep,
  Search,
  SideNav, SideNavItems, SideNavLink,
  Tab, TabList, TabPanel, TabPanels, Tabs,
  Tag,
  TextArea, TextInput,
  Tile,
  Toggle,
} from '@carbon/react';

const rows = [
  { id: '1', name: 'Alpha', owner: 'Ada', status: 'open', updated: '2026-10-01' },
  { id: '2', name: 'Beta', owner: 'Grace', status: 'pending', updated: '2026-10-02' },
  { id: '3', name: 'Gamma', owner: 'Alan', status: 'closed', updated: '2026-10-03' },
];
'''

TEMPLATES = {
    "table": '''
export default function TaskView() {
  const [q, setQ] = useState('');
  const headers = [
    { key: 'name', header: 'Name' },
    { key: 'owner', header: 'Owner' },
    { key: 'status', header: 'Status' },
    { key: 'updated', header: 'Updated' },
  ];
  const filtered = useMemo(() => rows.filter((r) => r.name.toLowerCase().includes(q.toLowerCase())), [q]);
  return (
    <Grid>
      <Column lg={16} md={8} sm={4}>
        <DataTable rows={filtered} headers={headers} isSortable>
          {({ rows, headers, getHeaderProps, getRowProps, getSelectionProps, getToolbarProps, getBatchActionProps, selectedRows }) => (
            <TableContainer title="Pending items" description="Select rows to act in batch">
              <TableToolbar {...getToolbarProps()}>
                <TableBatchActions {...getBatchActionProps()}>
                  <TableBatchAction tabIndex={getBatchActionProps().shouldShowBatchActions ? 0 : -1} onClick={() => undefined}>
                    Confirm
                  </TableBatchAction>
                </TableBatchActions>
                <TableToolbarContent>
                  <TableToolbarSearch value={q} onChange={(e: any) => setQ(e.target?.value ?? '')} persistent />
                  <Button kind="primary" size="sm">Primary action</Button>
                </TableToolbarContent>
              </TableToolbar>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableSelectAll {...getSelectionProps()} />
                    {headers.map((h: any) => <TableHeader {...getHeaderProps({ header: h })}>{h.header}</TableHeader>)}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((row: any) => (
                    <TableRow {...getRowProps({ row })}>
                      <TableSelectRow {...getSelectionProps({ row })} />
                      {row.cells.map((cell: any) => (
                        <TableCell key={cell.id}>
                          {cell.info.header === 'status' ? (
                            <Tag type={cell.value === 'open' ? 'green' : cell.value === 'pending' ? 'warm-gray' : 'gray'}>{cell.value}</Tag>
                          ) : cell.value}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DataTable>
      </Column>
    </Grid>
  );
}
''',
    "form": '''
export default function TaskView() {
  const [invalid, setInvalid] = useState(false);
  return (
    <Grid>
      <Column lg={8} md={4} sm={4}>
        <Form onSubmit={(e) => e.preventDefault()}>
          <FormGroup legendText="Register">
            <TextInput id="display-name" labelText="Display name" helperText="Shown to other people" />
            <TextInput id="email" type="email" labelText="Email" />
            <NumberInput id="ident" label="Numeric identifier" invalid={invalid} invalidText="Must be a positive integer" onChange={() => setInvalid(false)} />
            <TextArea id="notes" labelText="Notes" helperText="Optional context" />
          </FormGroup>
          <ButtonSet>
            <Button kind="secondary" type="button">Cancel</Button>
            <Button kind="primary" type="submit">Submit</Button>
          </ButtonSet>
        </Form>
      </Column>
    </Grid>
  );
}
''',
    "kpi-grid": '''
export default function TaskView() {
  const cards = [
    { title: 'Primary metric', value: '128', change: '+4.2%', up: true },
    { title: 'Open items', value: '17', change: '-1.1%', up: false },
    { title: 'Failures (24h)', value: '2', change: '0%', up: true },
    { title: 'Median age', value: '3.4d', change: '-8%', up: true },
  ];
  return (
    <Grid>
      {cards.map((c) => (
        <Column key={c.title} lg={4} md={4} sm={4}>
          <Tile>
            <p className="cds--type-label-01" style={{ color: 'var(--cds-text-secondary)' }}>{c.title}</p>
            <p className="cds--type-heading-03" style={{ color: 'var(--cds-text-primary)' }}>{c.value}</p>
            <p style={{ color: c.up ? 'var(--cds-support-success)' : 'var(--cds-support-error)' }}>{c.change}</p>
          </Tile>
        </Column>
      ))}
    </Grid>
  );
}
''',
    "modal": '''
export default function TaskView() {
  const [open, setOpen] = useState(true);
  const [typed, setTyped] = useState('');
  const name = 'Alpha';
  return (
    <Modal
      open={open}
      danger
      modalHeading="Confirm irreversible action"
      primaryButtonText="Confirm"
      secondaryButtonText="Cancel"
      primaryButtonDisabled={typed !== name}
      onRequestClose={() => setOpen(false)}
      onRequestSubmit={() => setOpen(false)}
    >
      <ModalHeader />
      <ModalBody>
        <p style={{ color: 'var(--cds-text-primary)' }}>
          This cannot be undone. Type the name to confirm.
        </p>
        <TextInput id="confirm-name" labelText="Name" value={typed} onChange={(e) => setTyped(e.target.value)} />
      </ModalBody>
      <ModalFooter />
    </Modal>
  );
}
''',
    "shell-nav": '''
export default function TaskView() {
  return (
    <>
      <Header aria-label="Product">
        <HeaderMenuButton aria-label="Open menu" onClick={() => undefined} />
        <HeaderName href="#" prefix="IBM">Workspace</HeaderName>
        <HeaderGlobalBar />
      </Header>
      <SideNav aria-label="Side navigation" expanded isRail>
        <SideNavItems>
          <SideNavLink href="#items">Items</SideNavLink>
          <SideNavLink href="#activity">Activity</SideNavLink>
          <SideNavLink href="#settings">Settings</SideNavLink>
        </SideNavItems>
      </SideNav>
      <Content>
        <Grid>
          <Column lg={16} md={8} sm={4}>
            <Breadcrumb>
              <BreadcrumbItem href="#">Home</BreadcrumbItem>
              <BreadcrumbItem href="#">Workspace</BreadcrumbItem>
              <BreadcrumbItem isCurrentPage>Overview</BreadcrumbItem>
            </Breadcrumb>
          </Column>
        </Grid>
      </Content>
    </>
  );
}
''',
    "notification": '''
export default function TaskView() {
  const [ok, setOk] = useState(true);
  return (
    <Grid>
      <Column lg={8} md={8} sm={4}>
        {ok ? (
          <InlineNotification
            kind="success"
            title="Operation succeeded"
            subtitle="The record was updated. You can keep working."
            onClose={() => undefined}
          />
        ) : (
          <ActionableNotification
            kind="error"
            title="Operation failed"
            subtitle="The service rejected the request."
            actionButtonLabel="Retry"
            onActionButtonClick={() => setOk(true)}
            onClose={() => undefined}
          />
        )}
      </Column>
    </Grid>
  );
}
''',
    "wizard": '''
export default function TaskView() {
  const [step, setStep] = useState(0);
  return (
    <Grid>
      <Column lg={16} md={8} sm={4}>
        <ProgressIndicator currentIndex={step}>
          <ProgressStep label="Review" />
          <ProgressStep label="Impact" />
          <ProgressStep label="Finish" />
        </ProgressIndicator>
        <Form>
          {step === 0 && <p style={{ color: 'var(--cds-text-primary)' }}>Review the details before continuing.</p>}
          {step === 1 && <p style={{ color: 'var(--cds-text-secondary)' }}>Confirm the impact of this change.</p>}
          {step === 2 && <p style={{ color: 'var(--cds-text-primary)' }}>This last step is irreversible.</p>}
          <ButtonSet>
            <Button kind="secondary" disabled={step === 0} onClick={() => setStep((s) => s - 1)}>Back</Button>
            {step < 2 ? (
              <Button kind="primary" onClick={() => setStep((s) => s + 1)}>Continue</Button>
            ) : (
              <Button kind="danger" onClick={() => undefined}>Confirm</Button>
            )}
          </ButtonSet>
        </Form>
      </Column>
    </Grid>
  );
}
''',
    "settings": '''
export default function TaskView() {
  const [typed, setTyped] = useState('');
  return (
    <Grid>
      <Column lg={16} md={8} sm={4}>
        <Tabs>
          <TabList aria-label="Settings sections">
            <Tab>Profile</Tab>
            <Tab>Notifications</Tab>
            <Tab>Danger zone</Tab>
          </TabList>
          <TabPanels>
            <TabPanel>
              <Form>
                <TextInput id="set-name" labelText="Display name" />
                <TextInput id="set-email" type="email" labelText="Email" />
                <Button kind="primary" type="submit">Save</Button>
              </Form>
            </TabPanel>
            <TabPanel>
              <Toggle id="notify" labelText="Email notifications" />
            </TabPanel>
            <TabPanel>
              <p style={{ color: 'var(--cds-text-secondary)' }}>This action is irreversible.</p>
              <TextInput id="set-confirm" labelText="Type the name to confirm" value={typed} onChange={(e) => setTyped(e.target.value)} />
              <Button kind="danger" disabled={typed.length === 0}>Delete</Button>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Column>
    </Grid>
  );
}
''',
}


def main() -> None:
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    tasks = [t for t in load_tasks() if t.gold]
    unused_imports = "Accordion, AccordionItem, Dropdown, Search,"
    header = HEADER.replace(unused_imports, "")
    for t in tasks:
        body = TEMPLATES[t.pattern]
        path = GOLD_DIR / f"{t.id}.tsx"
        path.write_text(header + body, encoding="utf-8")
        print("wrote", path.name, t.pattern)
    print(f"{len(tasks)} gold files")


if __name__ == "__main__":
    main()
