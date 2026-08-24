import React, { useEffect, useState } from 'react';
import {
  AppBar, Box, Chip, CircularProgress, Dialog, DialogContent, DialogTitle,
  Divider, Drawer, List, ListItemButton, ListItemIcon, ListItemText, Paper,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Toolbar,
  Typography, Grid, Card, CardContent, Link,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import WidgetsIcon from '@mui/icons-material/Widgets';
import { getSummary, getAssets, getAsset, getJobs } from './api.js';

const DRAWER = 220;

const STATUS_COLOR = { success: 'success', error: 'error', warning: 'warning', started: 'default' };

function StatCard({ label, value }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="overline" color="text.secondary">{label}</Typography>
        <Typography variant="h4">{value ?? '—'}</Typography>
      </CardContent>
    </Card>
  );
}

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [err, setErr] = useState(null);

  useEffect(() => {
    Promise.all([getSummary(), getJobs()])
      .then(([s, j]) => { setSummary(s); setJobs(j); })
      .catch((e) => setErr(String(e)));
  }, []);

  if (err) return <Typography color="error">Couldn’t reach the BFF: {err}</Typography>;
  if (!summary) return <CircularProgress />;

  const c = summary.counts || {};
  const inv = summary.latest_inventory;
  return (
    <Box>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}><StatCard label="Divi Assets" value={c.assets} /></Grid>
        <Grid item xs={6} md={3}><StatCard label="Asset Versions" value={c.asset_versions} /></Grid>
        <Grid item xs={6} md={3}><StatCard label="Inventory Snapshots" value={c.inventory_snapshots} /></Grid>
        <Grid item xs={6} md={3}><StatCard label="Jobs Logged" value={c.jobs} /></Grid>
      </Grid>

      {inv && (
        <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Latest inventory snapshot — {inv.kind} · {inv.environment}/{inv.site} · {new Date(inv.taken_at).toLocaleString()}
          </Typography>
          <Typography variant="body2">
            {inv.summary?.counts &&
              `${inv.summary.counts.pages} pages · ${inv.summary.counts.posts} posts · ${inv.summary.counts.media} media · ${inv.summary.counts.et_pb_layout_library} library items`}
          </Typography>
        </Paper>
      )}

      <Typography variant="h6" gutterBottom>Recent pipeline jobs</Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Job</TableCell><TableCell>Status</TableCell>
              <TableCell>When</TableCell><TableCell align="right">Duration</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {jobs.map((j) => (
              <TableRow key={j.id}>
                <TableCell>{j.job}</TableCell>
                <TableCell><Chip size="small" label={j.status} color={STATUS_COLOR[j.status] || 'default'} /></TableCell>
                <TableCell>{new Date(j.ran_at).toLocaleString()}</TableCell>
                <TableCell align="right">{j.duration_ms != null ? `${j.duration_ms} ms` : '—'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

function Assets() {
  const [assets, setAssets] = useState(null);
  const [detail, setDetail] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    getAssets().then(setAssets).catch((e) => setErr(String(e)));
  }, []);

  const open = (key) => getAsset(key).then(setDetail).catch((e) => setErr(String(e)));

  if (err) return <Typography color="error">{err}</Typography>;
  if (!assets) return <CircularProgress />;

  return (
    <Box>
      <Typography variant="h6" gutterBottom>Divi asset library</Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Key</TableCell><TableCell>Type</TableCell><TableCell>Title</TableCell>
              <TableCell>Lang</TableCell><TableCell>Status</TableCell>
              <TableCell align="right">WP post</TableCell><TableCell align="right">v</TableCell>
              <TableCell>Updated</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {assets.map((a) => (
              <TableRow key={a.asset_key} hover sx={{ cursor: 'pointer' }} onClick={() => open(a.asset_key)}>
                <TableCell><code>{a.asset_key}</code></TableCell>
                <TableCell><Chip size="small" label={a.asset_type} /></TableCell>
                <TableCell>{a.title}</TableCell>
                <TableCell>{a.language || '—'}</TableCell>
                <TableCell><Chip size="small" color={a.status === 'active' ? 'success' : 'default'} label={a.status} /></TableCell>
                <TableCell align="right">{a.wp_post_id ?? '—'}</TableCell>
                <TableCell align="right">{a.current_version}</TableCell>
                <TableCell>{new Date(a.updated_at).toLocaleDateString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={!!detail} onClose={() => setDetail(null)} maxWidth="md" fullWidth>
        {detail && (
          <>
            <DialogTitle>
              {detail.asset.title} <Chip size="small" label={detail.asset.asset_type} sx={{ ml: 1 }} />
            </DialogTitle>
            <DialogContent dividers>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                key <code>{detail.asset.asset_key}</code>
                {detail.asset.wp_post_id && <> · WP post {detail.asset.wp_post_id}</>}
                {' · '}source {detail.asset.source}
              </Typography>
              <Typography variant="subtitle2" sx={{ mt: 2 }}>Versions</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow><TableCell>v</TableCell><TableCell>Format</TableCell><TableCell>Checksum</TableCell><TableCell>By</TableCell><TableCell>Created</TableCell></TableRow>
                </TableHead>
                <TableBody>
                  {detail.versions.map((v) => (
                    <TableRow key={v.version}>
                      <TableCell>{v.version}</TableCell>
                      <TableCell>{v.content_format}</TableCell>
                      <TableCell><code>{(v.checksum || '').slice(0, 12)}</code></TableCell>
                      <TableCell>{v.created_by}</TableCell>
                      <TableCell>{new Date(v.created_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </DialogContent>
          </>
        )}
      </Dialog>
    </Box>
  );
}

export default function App() {
  const [view, setView] = useState('dashboard');
  const nav = [
    { id: 'dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
    { id: 'assets', label: 'Divi Assets', icon: <WidgetsIcon /> },
  ];
  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap>Vertical Console</Typography>
          <Chip label="v0" size="small" sx={{ ml: 1, bgcolor: 'rgba(255,255,255,.2)', color: '#fff' }} />
          <Box sx={{ flexGrow: 1 }} />
          <Typography variant="caption">local · vertical-web.ddev.site</Typography>
        </Toolbar>
      </AppBar>
      <Drawer variant="permanent" sx={{ width: DRAWER, flexShrink: 0, [`& .MuiDrawer-paper`]: { width: DRAWER, boxSizing: 'border-box' } }}>
        <Toolbar />
        <List>
          {nav.map((n) => (
            <ListItemButton key={n.id} selected={view === n.id} onClick={() => setView(n.id)}>
              <ListItemIcon>{n.icon}</ListItemIcon>
              <ListItemText primary={n.label} />
            </ListItemButton>
          ))}
        </List>
        <Divider />
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        {view === 'dashboard' ? <Dashboard /> : <Assets />}
      </Box>
    </Box>
  );
}
