import React, { useMemo, useState } from 'react';
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
