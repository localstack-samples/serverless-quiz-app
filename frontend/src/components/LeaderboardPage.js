import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  List,
  ListItem,
  ListItemText,
  Button,
  Box,
  CircularProgress,
  Alert,
  Paper,
  Stack,
} from '@mui/material';

function LeaderboardPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { quizID } = state || {};
  const [leaderboardData, setLeaderboardData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!quizID) {
      navigate('/');
      return;
    }

    fetch(`${process.env.REACT_APP_API_ENDPOINT}/getleaderboard?quiz_id=${quizID}&top=5`)
      .then((res) => res.json())
      .then((data) => {
        setLeaderboardData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching leaderboard data:', err);
        setError('Failed to fetch leaderboard data. Please try again later.');
        setLoading(false);
      });
  }, [quizID, navigate]);

  const handleGoHome = () => {
    navigate('/');
  };

  const handleViewEmailDemo = () => {
    let targetURL = '';
    const hostname = window.location.hostname;

    if (hostname.includes('localhost')) {
      targetURL = `http://localhost:4566/_extension/mailhog/`;
    } else {
      const baseOrigin = window.location.origin;
      targetURL = `${baseOrigin}/_extension/mailhog/`;
    }

    window.open(targetURL, '_blank');
  };

  if (loading) {
    return (
      <Container maxWidth="sm" sx={{ textAlign: 'center', marginTop: 8 }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ marginTop: 2 }}>
          Loading leaderboard...
        </Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="sm" sx={{ textAlign: 'center', marginTop: 8 }}>
        <Alert severity="error" sx={{ marginBottom: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" color="primary" onClick={handleGoHome}>
          Go to Home
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="md">
      <Box sx={{ textAlign: 'center', marginTop: 4 }}>
        <Typography variant="h4" gutterBottom>
          Leaderboard
        </Typography>
        {leaderboardData.length > 0 ? (
          <List component={Paper} sx={{ margin: '0 auto', maxWidth: 600 }}>
            {leaderboardData.map((entry, index) => (
              <ListItem key={index}>
                <ListItemText
                  primary={`${index + 1}. ${entry.Username}`}
                  secondary={`Score: ${entry.Score}`}
                />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography>No entries yet. Be the first to take the quiz!</Typography>
        )}

        <Box sx={{ marginTop: 4 }}>
          <Stack spacing={2} direction="row" justifyContent="center">
            <Button variant="contained" color="primary" onClick={handleGoHome}>
              Go to Home
            </Button>
            <Button variant="contained" color="secondary" onClick={handleViewEmailDemo}>
              View Email (Demo)
            </Button>
          </Stack>
        </Box>
      </Box>
    </Container>
  );
}

export default LeaderboardPage;
