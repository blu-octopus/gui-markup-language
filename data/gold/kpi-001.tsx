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
