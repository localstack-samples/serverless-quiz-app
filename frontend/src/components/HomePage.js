import React, { useState, useEffect } from 'react';
import {
  TextField,
  Button,
  Container,
  Typography,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  Stack,
  Alert,
  Box,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import QRCode from 'react-qr-code';

function HomePage() {
  const [quizID, setQuizID] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [publicQuizzes, setPublicQuizzes] = useState([]);
  const [selectedQuizID, setSelectedQuizID] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${process.env.REACT_APP_API_ENDPOINT}/listquizzes`)
      .then((res) => res.json())
      .then((data) => {
        if (data && Array.isArray(data.Quizzes) && data.Quizzes.length > 0) {
          setPublicQuizzes(data.Quizzes);
        } else {
          setPublicQuizzes([]);
        }
      })
      .catch((err) => {
        console.error('Error fetching public quizzes:', err);
        setPublicQuizzes([]);
      });
  }, []);

  const validateEmail = (email) => {
    if (!email) return true;
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  const handleStart = () => {
    if (!validateEmail(email)) {
      setErrorMessage('Please enter a valid email address.');
      return;
    }
    setErrorMessage('');
    navigate('/quiz', { state: { quizID, username, email } });
  };

  const handleQuizSelect = (event) => {
    const selectedQuizID = event.target.value;
    setSelectedQuizID(selectedQuizID);
    setQuizID(selectedQuizID);
  };

  const handleQuizIDChange = (e) => {
    setQuizID(e.target.value);
    setSelectedQuizID('');
  };

  const handleCreateQuiz = () => {
    navigate('/create-quiz');
  };

  // Get the current page URL
  const pageURL = window.location.href;

  return (
    <Container maxWidth="sm">
      <Typography variant="h4" gutterBottom>
        Enter Quiz Details
      </Typography>

      {errorMessage && (
        <Alert severity="error" sx={{ marginBottom: 2 }}>
          {errorMessage}
        </Alert>
      )}

      {publicQuizzes.length > 0 ? (
        <FormControl fullWidth margin="normal">
          <InputLabel id="public-quiz-label">Select a Public Quiz</InputLabel>
          <Select
            labelId="public-quiz-label"
            value={selectedQuizID}
            label="Select a Public Quiz"
            onChange={handleQuizSelect}
          >
            {publicQuizzes.map((quiz) => (
              <MenuItem key={quiz.QuizID} value={quiz.QuizID}>
                {quiz.Title}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      ) : (
        <Typography variant="body1" gutterBottom>
          No public quizzes are available.
        </Typography>
      )}

      <TextField
        label="Quiz ID"
        fullWidth
        margin="normal"
        value={quizID}
        onChange={handleQuizIDChange}
        disabled={selectedQuizID !== ''}
      />
      <TextField
        label="Username"
        fullWidth
        margin="normal"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <TextField
        label="Email (Optional)"
        fullWidth
        margin="normal"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      <Stack spacing={2} marginTop={4}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleStart}
          disabled={!quizID || !username}
        >
          Start Playing
        </Button>
        <Button
          variant="contained"
          color="secondary"
          onClick={handleCreateQuiz}
        >
          Create a New Quiz
        </Button>
      </Stack>

      <Box sx={{ marginTop: 4, textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom>
          Share this Page
        </Typography>
        <Box
          sx={{
            background: 'white',
            display: 'inline-block',
            padding: '16px',
          }}
        >
          <QRCode value={pageURL} size={128} />
        </Box>
      </Box>
    </Container>
  );
}

export default HomePage;
