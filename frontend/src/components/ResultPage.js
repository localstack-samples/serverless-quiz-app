import React, { useEffect, useState, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Button,
  CircularProgress,
  Box,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';

function ResultPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { submissionID, quizID } = state || {};
  const [resultData, setResultData] = useState(null);
  const [quizData, setQuizData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const attemptsRef = useRef(0);
  const maxAttempts = 10;
  const pollingInterval = 3000;
  const timeoutIdRef = useRef(null);

  useEffect(() => {
    if (!submissionID || !quizID) {
      navigate('/');
      return;
    }

    fetch(`${process.env.REACT_APP_API_ENDPOINT}/getquiz?quiz_id=${quizID}`)
      .then((res) => res.json())
      .then((data) => {
        setQuizData(data);
      })
      .catch((err) => {
        console.error('Error fetching quiz data:', err);
        setError('Failed to fetch quiz data. Please try again later.');
        setLoading(false);
      });

    const fetchResult = () => {
      fetch(`${process.env.REACT_APP_API_ENDPOINT}/getsubmission?submission_id=${submissionID}`)
        .then((res) => {
          if (!res.ok) {
            throw new Error('Result not ready yet.');
          }
          return res.json();
        })
        .then((data) => {
          setResultData(data);
          setLoading(false);
        })
        .catch((err) => {
          console.error('Error fetching result:', err);
          attemptsRef.current += 1;
          if (attemptsRef.current >= maxAttempts) {
            setError('Failed to fetch results. Please try again later.');
            setLoading(false);
          } else {
            // Schedule the next fetch
            timeoutIdRef.current = setTimeout(fetchResult, pollingInterval);
          }
        });
    };
    fetchResult();
    return () => {
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
      }
    };
  }, [submissionID, quizID, navigate]);

  const handleViewLeaderboard = () => {
    navigate('/leaderboard', { state: { quizID } });
  };

  const handleGoHome = () => {
    navigate('/');
  };

  if (loading || !quizData) {
    return (
      <Container maxWidth="sm" sx={{ textAlign: 'center', marginTop: 8 }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ marginTop: 2 }}>
          Processing your submission...
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
          Quiz Results
        </Typography>
        <Typography variant="h6" gutterBottom>
          Total Score: {resultData.Score}
        </Typography>
        {resultData.UserAnswers && quizData.Questions && (
          <Box sx={{ marginTop: 4 }}>
            <Typography variant="h5" gutterBottom>
              Detailed Results
            </Typography>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Question</TableCell>
                    <TableCell>Your Answer</TableCell>
                    <TableCell>Time Taken (s)</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {quizData.Questions.map((question, index) => (
                    <TableRow key={index}>
                      <TableCell>{question.QuestionText}</TableCell>
                      <TableCell>
                        {resultData.UserAnswers[index]?.Answer || 'No Answer'}
                      </TableCell>
                      <TableCell>
                        {resultData.UserAnswers[index]?.TimeTaken ?? 'N/A'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        <Box sx={{ marginTop: 4 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleViewLeaderboard}
            sx={{ marginRight: 2 }}
          >
            View Leaderboard
          </Button>
          <Button variant="outlined" color="secondary" onClick={handleGoHome}>
            Go to Home
          </Button>
        </Box>
      </Box>
    </Container>
  );
}

export default ResultPage;
