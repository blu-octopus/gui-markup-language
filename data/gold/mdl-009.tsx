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
