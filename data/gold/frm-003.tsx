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
