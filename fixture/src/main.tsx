import React from 'react';
import { createRoot } from 'react-dom/client';
import '@carbon/react/index.scss';
import TaskView from './TaskView';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <TaskView />
  </React.StrictMode>,
);
