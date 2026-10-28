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
