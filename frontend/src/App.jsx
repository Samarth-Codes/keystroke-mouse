import React, { useState, useRef, useEffect } from 'react';
import { Container, Box, Typography, TextField, Button, Alert, Paper, CircularProgress } from '@mui/material';
import { motion } from 'framer-motion';
import './App.css';

const PASS = 'open sesame';

function App() {
  const [username, setUsername] = useState('');
  const [passphrase, setPassphrase] = useState('');
  const [msg, setMsg] = useState('');
  const [expectedCount, setExpectedCount] = useState(27);
  const [expectedCountMsg, setExpectedCountMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [featureCountError, setFeatureCountError] = useState(false);
  const keyTimes = useRef([]);
  const mouseMoves = useRef([]);
  const mouseClicks = useRef(0);
  const typingStart = useRef(null);
  const typingEnd = useRef(null);
  const backspaceCount = useRef(0);
  const lastMouse = useRef(null);

  // Fetch expected feature count
  const fetchExpectedFeatureCount = async (user = username) => {
    let url = '/expected_feature_count';
    if (user) url += `?username=${encodeURIComponent(user)}`;
    try {
      const res = await fetch(url);
      const data = await res.json();
      setExpectedCount(data.expected_feature_count);
      setExpectedCountMsg(`Expected feature count: ${data.expected_feature_count}`);
    } catch (e) {
      setExpectedCountMsg('Could not fetch expected feature count.');
    }
  };

  useEffect(() => {
    fetchExpectedFeatureCount();
    // Mouse move/click listeners
    const handleMouseMove = (e) => {
      if (!lastMouse.current) lastMouse.current = { x: e.clientX, y: e.clientY, t: performance.now() };
      else {
        const now = performance.now();
        const dx = e.clientX - lastMouse.current.x;
        const dy = e.clientY - lastMouse.current.y;
        const dt = now - lastMouse.current.t;
        mouseMoves.current.push({ dx, dy, dt });
        lastMouse.current = { x: e.clientX, y: e.clientY, t: now };
      }
    };
    const handleMouseDown = () => { mouseClicks.current++; };
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mousedown', handleMouseDown);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
    };
    // eslint-disable-next-line
  }, []);

  // Keystroke listeners
  useEffect(() => {
    const input = document.getElementById('passphrase-input');
    if (!input) return;
    const handleKeyDown = (e) => {
      if (!typingStart.current) typingStart.current = performance.now();
      if (e.key.length === 1) {
        keyTimes.current.push({ key: e.key, down: performance.now(), up: null });
      }
      if (e.key === 'Backspace') backspaceCount.current++;
    };
    const handleKeyUp = (e) => {
      typingEnd.current = performance.now();
      let idx = keyTimes.current.findIndex(k => k.key === e.key && k.up === null);
      if (idx !== -1) keyTimes.current[idx].up = performance.now();
    };
    input.addEventListener('keydown', handleKeyDown);
    input.addEventListener('keyup', handleKeyUp);
    return () => {
      input.removeEventListener('keydown', handleKeyDown);
      input.removeEventListener('keyup', handleKeyUp);
    };
  }, [passphrase]);

  // Feature extraction
  function extractFeatures() {
    if (passphrase !== PASS) {
      setMsg('Passphrase incorrect!');
      return null;
    }
    let holds = [], intervals = [];
    for (let i = 0; i < keyTimes.current.length; ++i) {
      if (keyTimes.current[i].up && keyTimes.current[i].down) {
        holds.push(keyTimes.current[i].up - keyTimes.current[i].down);
      }
      if (i > 0 && keyTimes.current[i].down && keyTimes.current[i - 1].down) {
        intervals.push(keyTimes.current[i].down - keyTimes.current[i - 1].down);
      }
    }
    let typingDuration = typingEnd.current && typingStart.current ? (typingEnd.current - typingStart.current) : 1;
    let typingSpeed = passphrase.length / (typingDuration / 1000);
    let totalDist = 0, totalTime = 0;
    for (let m of mouseMoves.current) {
      totalDist += Math.sqrt(m.dx * m.dx + m.dy * m.dy);
      totalTime += m.dt;
    }
    let avgSpeed = totalTime > 0 ? totalDist / (totalTime / 1000) : 0;
    let userAgent = navigator.userAgent;
    let features = holds.concat(intervals);
    features.push(typingSpeed);
    features.push(backspaceCount.current);
    features.push(avgSpeed);
    features.push(totalDist);
    features.push(mouseClicks.current);
    let uaHash = 0;
    for (let i = 0; i < userAgent.length; ++i) uaHash += userAgent.charCodeAt(i);
    features.push(uaHash);
    // Reset
    keyTimes.current = [];
    mouseMoves.current = [];
    mouseClicks.current = 0;
    typingStart.current = null;
    typingEnd.current = null;
    backspaceCount.current = 0;
    lastMouse.current = null;
    return features;
  }

  function checkFeatureCount(feats) {
    if (feats.length !== expectedCount) {
      setMsg(`Feature count mismatch! Expected ${expectedCount}, got ${feats.length}. Please type the passphrase exactly and try again.`);
      setPassphrase('');
      setFeatureCountError(true);
      return false;
    }
    setFeatureCountError(false);
    return true;
  }

  // Enroll
  const enroll = async () => {
    setLoading(true);
    setMsg('');
    const feats = extractFeatures();
    if (!feats || !username) { setLoading(false); return; }
    if (!checkFeatureCount(feats)) { setLoading(false); return; }
    const res = await fetch('/enroll', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, features: feats })
    });
    const data = await res.json();
    setMsg(JSON.stringify(data) + '\nFeature count: ' + feats.length);
    setPassphrase('');
    setLoading(false);
  };

  // Authenticate
  const authenticate = async () => {
    setLoading(true);
    setMsg('');
    const feats = extractFeatures();
    if (!feats || !username) { setLoading(false); return; }
    if (!checkFeatureCount(feats)) { setLoading(false); return; }
    const res = await fetch('/authenticate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, features: feats })
    });
    const data = await res.json();
    setMsg(JSON.stringify(data) + '\nFeature count: ' + feats.length + (data.model_type ? ('\nModel: ' + data.model_type) : ''));
    setPassphrase('');
    setLoading(false);
  };

  return (
    <Box
      width="100vw"
      minHeight="100vh"
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      className="animated-bg"
      sx={{ overflowX: 'hidden' }}
    >
      <Container maxWidth="sm">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        >
          <Paper
            elevation={6}
            className="animated-paper"
            sx={{ p: { xs: 2, sm: 4 }, borderRadius: 3, width: { xs: '100%', sm: 450 }, mx: 'auto' }}
            component={motion.div}
            whileHover={{ scale: 1.025, boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.25)' }}
            transition={{ type: 'spring', stiffness: 300 }}
          >
            <Typography variant="h4" align="center" gutterBottom>
              Keystroke & Mouse Dynamics Auth Test
            </Typography>
            <Typography variant="subtitle1" align="center" gutterBottom>
              Type the passphrase: <b>open sesame</b>
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              <TextField
                label="Username"
                value={username}
                onChange={e => { setUsername(e.target.value); fetchExpectedFeatureCount(e.target.value); }}
                onBlur={() => fetchExpectedFeatureCount()}
                autoComplete="off"
                fullWidth
                className="animated-input"
              />
              <TextField
                id="passphrase-input"
                label="Passphrase"
                value={passphrase}
                onChange={e => setPassphrase(e.target.value)}
                autoComplete="off"
                fullWidth
                error={featureCountError}
                helperText={featureCountError ? 'Please type the passphrase exactly.' : ''}
                className="animated-input"
              />
              <Box display="flex" gap={2} justifyContent="center">
                <motion.div whileHover={{ scale: 1.08 }} whileTap={{ scale: 0.97 }}>
                  <Button variant="contained" color="primary" onClick={enroll} disabled={loading}>
                    {loading ? <CircularProgress size={24} /> : 'Enroll'}
                  </Button>
                </motion.div>
                <motion.div whileHover={{ scale: 1.08 }} whileTap={{ scale: 0.97 }}>
                  <Button variant="contained" color="secondary" onClick={authenticate} disabled={loading}>
                    {loading ? <CircularProgress size={24} /> : 'Authenticate'}
                  </Button>
                </motion.div>
              </Box>
              {msg && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
                  <Alert severity={msg.includes('incorrect') || msg.includes('mismatch') ? 'error' : 'info'} sx={{ whiteSpace: 'pre-line' }}>{msg}</Alert>
                </motion.div>
              )}
              {expectedCountMsg && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
                  <Alert severity="info">{expectedCountMsg}</Alert>
                </motion.div>
              )}
            </Box>
          </Paper>
        </motion.div>
      </Container>
      {/* Instructions Section */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1.2, ease: 'easeOut' }}
        style={{ width: '100%' }}
      >
        <Box mt={4} maxWidth={600} px={2} mx="auto">
          <Paper elevation={0} sx={{ background: 'transparent', p: 2 }}>
            <Typography variant="h6" gutterBottom>How to use:</Typography>
            <Typography variant="body1" gutterBottom>
              1. Enter your <b>username</b> in the Username field.<br />
              2. Carefully type the passphrase <b>open sesame</b> in the Passphrase field.<br />
              3. Click <b>Enroll</b> to register your keystroke and mouse dynamics.<br />
              4. Click <b>Authenticate</b> to verify your identity using your typing and mouse behavior.<br />
              5. For best results, type the passphrase exactly and avoid copy-pasting.<br />
              6. If you see a feature count mismatch, clear the passphrase and try again.
            </Typography>
          </Paper>
        </Box>
      </motion.div>
    </Box>
  );
}

export default App;
