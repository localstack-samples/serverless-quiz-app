import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  RadioGroup,
  FormControlLabel,
  Radio,
  Button,
  CircularProgress,
  Box,
  LinearProgress,
  Grid2 as Grid,
  Alert,
  IconButton,
} from '@mui/material';

import CloseIcon from '@mui/icons-material/Close';
import MainLayout from './QuizLayout';
import Mascot1 from '../Mascot1.svg';
import Mascot2 from '../Mascot2.svg';
import Mascot3 from '../Mascot3.svg';

function QuizPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { quizID, username, email } = state || {};
  const [quizData, setQuizData] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const timerRef = useRef(null);
  const questionStartTimeRef = useRef(null);
  const hasSubmittedRef = useRef(false);

  useEffect(() => {
    if (!quizID || !username) {
      navigate('/');
      return;
    }

    fetch(`${process.env.REACT_APP_API_ENDPOINT}/getquiz?quiz_id=${quizID}`)
      .then((res) => res.json())
      .then((data) => {
        setQuizData(data);
        if (data.EnableTimer) {
          setTimeLeft(data.TimerSeconds);
        }
        questionStartTimeRef.current = Date.now();
      })
      .catch((err) => {
        console.error('Error fetching quiz:', err);
        alert('Failed to load quiz. Please try again later.');
        navigate('/');
      });
  }, [quizID, username, navigate]);

  const handleSubmit = useCallback(
    (timerExceeded = false) => {
      if (hasSubmittedRef.current) return;
      hasSubmittedRef.current = true;

      setIsSubmitting(true);
      const submissionData = {
        Username: username,
        QuizID: quizID,
        Answers: answers,
      };
      if (email) {
        submissionData.Email = email;
      }
      if (timerExceeded) {
        submissionData.TimerExceeded = true;
      }

      fetch(`${process.env.REACT_APP_API_ENDPOINT}/submitquiz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(submissionData),
      })
        .then((res) => res.json())
        .then((data) => {
          navigate('/result', {
            state: { submissionID: data.SubmissionID, quizID },
          });
        })
        .catch((err) => {
          console.error('Error submitting quiz:', err);
          alert('Failed to submit quiz. Please try again.');
          setIsSubmitting(false);
          hasSubmittedRef.current = false;
        });
    },
    [username, quizID, answers, email, navigate]
  );

  const moveToNextQuestion = useCallback(() => {
    if (quizData && currentQuestionIndex < quizData.Questions.length - 1) {
      setCurrentQuestionIndex((prevIndex) => prevIndex + 1);
    }
  }, [quizData, currentQuestionIndex]);

  const handleSkip = () => {
    const timeTaken =
      quizData && quizData.EnableTimer ? quizData.TimerSeconds - timeLeft : 0;

    setAnswers((prevAnswers) => ({
      ...prevAnswers,
      [currentQuestionIndex]: {
        Answer: '',
        TimeTaken: timeTaken,
        Skipped: true,
      },
    }));

    if (quizData && quizData.EnableTimer && timerRef.current) {
      clearInterval(timerRef.current);
    }

    if (currentQuestionIndex < quizData.Questions.length - 1) {
      moveToNextQuestion();
    } else {
      if (!hasSubmittedRef.current) {
        handleSubmit();
      }
    }
  };

  useEffect(() => {
    if (quizData && quizData.EnableTimer) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }

      setTimeLeft(quizData.TimerSeconds);
      questionStartTimeRef.current = Date.now();

      const handleTimeUp = () => {
        const timeTaken = quizData.TimerSeconds;
        setAnswers((prevAnswers) => ({
          ...prevAnswers,
          [currentQuestionIndex]: {
            Answer: prevAnswers[currentQuestionIndex]?.Answer || '',
            TimeTaken: timeTaken,
          },
        }));

        if (currentQuestionIndex < quizData.Questions.length - 1) {
          moveToNextQuestion();
        } else {
          if (!hasSubmittedRef.current) {
            handleSubmit(true);
          }
        }
      };

      timerRef.current = setInterval(() => {
        setTimeLeft((prevTime) => {
          if (prevTime <= 1) {
            clearInterval(timerRef.current);
            handleTimeUp();
            return 0;
          }
          return prevTime - 1;
        });
      }, 1000);

      return () => clearInterval(timerRef.current);
    }
  }, [currentQuestionIndex, quizData, moveToNextQuestion, handleSubmit]);

  const handleOptionChange = (e) => {
    const selectedOption = e.target.value;
    const timeTaken =
      quizData && quizData.EnableTimer ? quizData.TimerSeconds - timeLeft : 0;

    setAnswers((prevAnswers) => ({
      ...prevAnswers,
      [currentQuestionIndex]: {
        Answer: selectedOption,
        TimeTaken: timeTaken,
      },
    }));

    if (quizData && quizData.EnableTimer && timerRef.current) {
      clearInterval(timerRef.current);
    }

    if (currentQuestionIndex < quizData.Questions.length - 1) {
      moveToNextQuestion();
    } else {
      if (!hasSubmittedRef.current) {
        handleSubmit();
      }
    }
  };

  let currentQuestion = null;
  if (quizData && quizData.Questions) {
    currentQuestion = quizData.Questions[currentQuestionIndex];
  }

  if (!quizData || !currentQuestion) {
    return (
      <Container maxWidth="md" sx={{ textAlign: 'center', marginTop: 8 }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ marginTop: 2 }}>
          Loading quiz...
        </Typography>
      </Container>
    );
  }

  const isTimeUp = quizData.EnableTimer && timeLeft <= 0;

  return (
    <MainLayout>
      <Container maxWidth="sm" className="main-quiz-container" sx={{ position: 'relative' }}>
        {/* Skip Button at Top Right */}
        {!isSubmitting && (
          <IconButton
            onClick={handleSkip}
            disabled={isSubmitting || isTimeUp}
            sx={{ position: 'absolute', top: 8, right: 8 }}
            aria-label="Skip"
          >
            <CloseIcon />
          </IconButton>
        )}

        <Typography variant="h6" gutterBottom align="left" width={'100%'}>
          Question {currentQuestionIndex + 1} / {quizData.Questions.length}
        </Typography>

        <Container maxWidth={'100%'} className="question-container">
          <Typography variant="h4" gutterBottom color="#EAEAF0" align="center">
            {currentQuestion.QuestionText}
          </Typography>
        </Container>

        {quizData.EnableTimer && (
          <Box sx={{ width: '100%', textAlign: 'center' }}>
            <Grid container spacing={2}>
              <Typography variant="body2" color="textSecondary" width={'8%'}>
                Time:
              </Typography>
              <LinearProgress
                variant="determinate"
                color="primary"
                value={(timeLeft / quizData.TimerSeconds) * 100}
                sx={{
                  height: 5,
                  borderRadius: 5,
                  width: '78%',
                  marginTop: '8px',
                }}
              />
              <Typography variant="body2" color="textSecondary" width={'8%'}>
                {timeLeft}
              </Typography>
            </Grid>
          </Box>
        )}
        <RadioGroup
          name={`question-${currentQuestionIndex}`}
          value={answers[currentQuestionIndex]?.Answer || ''}
          onChange={handleOptionChange}
          sx={{ width: '100%' }}
        >
          {currentQuestion.Options.map((option, idx) => (
            <FormControlLabel
              key={idx}
              value={option}
              control={<Radio />}
              label={option}
              disabled={isSubmitting || isTimeUp}
              sx={{
                borderRadius: '4px',
                border: '1px solid #D9DADF',
                background: '#EAEAF0',
                width: '100%',
                margin: '4px',
                textAlign: 'left',
              }}
            />
          ))}
        </RadioGroup>

        {!isSubmitting && currentQuestionIndex === quizData.Questions.length - 1 && (
          <Box sx={{ textAlign: 'center', marginTop: 4 }}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSubmit}
              disabled={isSubmitting || isTimeUp}
            >
              Submit Quiz
            </Button>
          </Box>
        )}

        {isSubmitting && (
          <Box sx={{ textAlign: 'center', marginTop: 4 }}>
            <CircularProgress />
            <Typography variant="h6" sx={{ marginTop: 2 }}>
              Submitting your answers...
            </Typography>
          </Box>
        )}
      </Container>
      <div className="character-container">
        {currentQuestionIndex % 3 === 0 && (
          <div className="character-box">
            <img src={Mascot1} alt="Mascot" />
          </div>
        )}
        {currentQuestionIndex % 3 === 1 && (
          <div className="character-box-right">
            <img src={Mascot2} alt="Mascot" />
          </div>
        )}
        {currentQuestionIndex % 3 === 2 && (
          <div className="character-box">
            <img src={Mascot3} alt="Mascot" />
          </div>
        )}
      </div>
      {currentQuestion.Trivia && (
        <Alert
          severity="info"
          sx={{
            marginTop: 4,
            textAlign: 'center',
            backgroundColor: '#E6EAFF',
            width: 320,
            marginLeft: 'auto',
            marginRight: 'auto',
            borderRadius: '4px',
          }}
        >
          <Typography
            variant="h5"
            color="textSecondary"
            align="left"
            sx={{ marginTop: 2 }}
          >
            Hint
          </Typography>
          <Typography
            variant="body2"
            align="left"
            color="textSecondary"
            sx={{ marginTop: 2 }}
          >
            {currentQuestion.Trivia}
          </Typography>
        </Alert>
      )}
    </MainLayout>
  );
}

export default QuizPage;
