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
