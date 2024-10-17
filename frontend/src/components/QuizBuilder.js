import React, { useState } from 'react';
import {
  Container,
  Typography,
  TextField,
  Button,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  FormControlLabel,
  RadioGroup,
  Radio,
  Card,
  CardContent,
  Grid,
  Stack,
  Alert,
  Switch,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

function QuizBuilder() {
  const [title, setTitle] = useState('');
  const [visibility, setVisibility] = useState('Public');
  const [enableTimer, setEnableTimer] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(30);
  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState({
    QuestionText: '',
    Options: ['', '', '', ''],
    CorrectAnswer: '',
    Trivia: '',
  });
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleOptionChange = (index, value) => {
    const newOptions = [...currentQuestion.Options];
    newOptions[index] = value;
    setCurrentQuestion({ ...currentQuestion, Options: newOptions });
  };

  const handleAddQuestion = () => {
    // Validate the current question
    const { QuestionText, Options, CorrectAnswer } = currentQuestion;
    if (
      !QuestionText.trim() ||
      Options.some((opt) => !opt.trim()) ||
      !CorrectAnswer.trim()
    ) {
      setErrorMessage('Please fill all fields and select a correct answer.');
      return;
    }
    setQuestions([...questions, currentQuestion]);
    setErrorMessage('');
    // Reset current question
    setCurrentQuestion({
      QuestionText: '',
      Options: ['', '', '', ''],
      CorrectAnswer: '',
      Trivia: '',
    });
  };

  const handleSubmitQuiz = () => {
    if (!title.trim() || questions.length === 0) {
      setErrorMessage('Please provide a title and add at least one question.');
      return;
    }

    if (enableTimer && (!timerSeconds || timerSeconds <= 0)) {
      setErrorMessage('Please enter a valid number of seconds for the timer.');
      return;
    }

    const quizData = {
      Title: title,
      Visibility: visibility,
      EnableTimer: enableTimer,
      TimerSeconds: enableTimer ? timerSeconds : undefined,
      Questions: questions,
    };

    setIsSubmitting(true); // Start submission

    fetch(`${process.env.REACT_APP_API_ENDPOINT}/createquiz`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(quizData),
    })
      .then(async (res) => {
        const contentType = res.headers.get('Content-Type');
        if (!contentType || !contentType.includes('application/json')) {
          throw new Error('Invalid response from server.');
        }

        const data = await res.json();

        if (!res.ok) {
          const errorMsg = data.message || 'Failed to create quiz.';
          throw new Error(errorMsg);
        }

        if (data.QuizID) {
          setSuccessMessage(`Quiz created successfully! Quiz ID: ${data.QuizID}`);
          // Optionally, navigate to another page after a short delay
          setTimeout(() => {
            navigate('/');
          }, 2000);
        } else {
          throw new Error('Quiz ID not returned from server.');
        }
      })
      .catch((err) => {
        console.error('Error creating quiz:', err);
        setErrorMessage(err.message);
      })
      .finally(() => {
        setIsSubmitting(false);
      });
  };

  return (
    <Container maxWidth="md">
      <Typography variant="h4" gutterBottom>
        Create a New Quiz
      </Typography>

      {errorMessage && (
        <Alert severity="error" sx={{ marginBottom: 2 }}>
          {errorMessage}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" sx={{ marginBottom: 2 }}>
          {successMessage}
        </Alert>
      )}

      <TextField
        label="Quiz Title"
        fullWidth
        margin="normal"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />

      <FormControl fullWidth margin="normal">
        <InputLabel id="visibility-label">Visibility</InputLabel>
        <Select
          labelId="visibility-label"
          value={visibility}
          label="Visibility"
          onChange={(e) => setVisibility(e.target.value)}
        >
          <MenuItem value="Public">Public</MenuItem>
          <MenuItem value="Private">Private</MenuItem>
        </Select>
      </FormControl>

      <FormControlLabel
        control={
          <Switch
            checked={enableTimer}
            onChange={(e) => setEnableTimer(e.target.checked)}
            color="primary"
          />
        }
        label="Enable Timer"
        sx={{ marginTop: 2 }}
      />

      {enableTimer && (
        <TextField
          label="Timer Seconds per Question"
          type="number"
          fullWidth
          margin="normal"
          value={timerSeconds}
          onChange={(e) => setTimerSeconds(parseInt(e.target.value, 10))}
          inputProps={{ min: 1 }}
        />
      )}

      <Card variant="outlined" sx={{ marginTop: 4 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            Add a Question
          </Typography>

          <TextField
            label="Question Text"
            fullWidth
            margin="normal"
            value={currentQuestion.QuestionText}
            onChange={(e) =>
              setCurrentQuestion({
                ...currentQuestion,
                QuestionText: e.target.value,
              })
            }
          />

          <Grid container spacing={2}>
            {currentQuestion.Options.map((option, index) => (
              <Grid item xs={12} sm={6} key={index}>
                <TextField
                  label={`Option ${index + 1}`}
                  fullWidth
                  value={option}
                  onChange={(e) => handleOptionChange(index, e.target.value)}
                />
              </Grid>
            ))}
          </Grid>

          <FormControl component="fieldset" margin="normal">
            <Typography variant="subtitle1">Correct Answer</Typography>
            <RadioGroup
              value={currentQuestion.CorrectAnswer}
              onChange={(e) =>
                setCurrentQuestion({
                  ...currentQuestion,
                  CorrectAnswer: e.target.value,
                })
              }
            >
              {currentQuestion.Options.map((option, index) => (
                <FormControlLabel
                  key={index}
                  value={option}
                  control={<Radio />}
                  label={`Option ${index + 1}`}
                  disabled={!option.trim()}
                />
              ))}
            </RadioGroup>
          </FormControl>

          <TextField
            label="Trivia (Optional)"
            fullWidth
            margin="normal"
            value={currentQuestion.Trivia}
            onChange={(e) =>
              setCurrentQuestion({ ...currentQuestion, Trivia: e.target.value })
            }
          />

          <Stack direction="row" spacing={2} marginTop={2}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleAddQuestion}
            >
              Add Question
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              onClick={() =>
                setCurrentQuestion({
                  QuestionText: '',
                  Options: ['', '', '', ''],
                  CorrectAnswer: '',
                  Trivia: '',
                })
              }
            >
              Clear
            </Button>
          </Stack>
        </CardContent>
      </Card>

      {questions.length > 0 && (
        <Card variant="outlined" sx={{ marginTop: 4 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Questions Added ({questions.length})
            </Typography>
            {questions.map((question, index) => (
              <Typography key={index} variant="body1" gutterBottom>
                {index + 1}. {question.QuestionText}
              </Typography>
            ))}
          </CardContent>
        </Card>
      )}

      <Stack spacing={2} marginTop={4}>
        <Button
          variant="contained"
          color="success"
          onClick={handleSubmitQuiz}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Quiz'}
        </Button>
        <Button variant="outlined" onClick={() => navigate('/')}>
          Cancel
        </Button>
      </Stack>
    </Container>
  );
}

export default QuizBuilder;
