"use client"
import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import {
    Box,
    Paper,
    Typography,
    Button,
    Divider,
    Modal,
    CircularProgress,
    Grid
} from '@mui/material';
import ArrowBackIosNewIcon from '@mui/icons-material/ArrowBackIosNew';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import GameComponent from './GameComponent';

type Match = {
    models: string[];
    game: string;
    result: number;
    message: string;
    turns: {
        context: {
            last_trace: Record<string, string>;
            history: string[];
            message: string | null;
        };
    }[];
};

const MatchPage = () => {
    const params = useParams();
    const matchId = params?.id;

    const [match, setMatch] = useState<Match | null>(null);
    const [currentTurn, setCurrentTurn] = useState(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchMatchData = async () => {
            try {
                setLoading(true);
                const response = await fetch(`/api/matches/${matchId}`);
                const data = await response.json();
                console.log('Match data:', data);
                setMatch(data);
            } catch (error) {
                console.error('Error fetching match data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchMatchData();
    }, [matchId]);

    const handlePrevTurn = () => {
        setCurrentTurn(prev => Math.max(0, prev - 1));
    };

    const handleNextTurn = () => {
        if (match) {
            setCurrentTurn(prev => Math.min(match?.turns.length - 1, prev + 1));
        }
    };

    if (loading) {
        return (
            <Modal
                open={loading}
                aria-labelledby="loading-modal-title"
                aria-describedby="loading-modal-description"
            >
                <Box sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    bgcolor: 'background.paper',
                    boxShadow: 24,
                    p: 4,
                    borderRadius: 2,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                }}>
                    <CircularProgress sx={{ mb: 2 }} />
                    <Typography id="loading-modal-title" variant="h6" component="h2">
                        Loading Match Data
                    </Typography>
                    <Typography id="loading-modal-description" sx={{ mt: 2 }}>
                        Please wait while we fetch the match details...
                    </Typography>
                </Box>
            </Modal>
        );
    }

    if (!match) {
        return <Typography>No match data available.</Typography>;
    }

    return (
        <Box sx={{ flexGrow: 1, p: 2 }}>
            <Grid container spacing={2}>
                {/* Game component and controls - will be at the top on narrow screens */}
                <Grid item xs={12} md={6} order={{ xs: 1, md: 2 }}>
                    <Paper sx={{ p: 2, mb: { xs: 2, md: 0 } }}>
                        <GameComponent turn={match?.turns[currentTurn]} moveNumber={currentTurn} lastMove={currentTurn == match?.turns.length - 1} />
                        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mt: 2 }}>
                            <Button onClick={handlePrevTurn} disabled={currentTurn === 0}>
                                <ArrowBackIosNewIcon />
                            </Button>
                            <Typography sx={{ mx: 2 }}>
                                Turn {currentTurn + 1} of {match?.turns.length}
                            </Typography>
                            <Button onClick={handleNextTurn} disabled={currentTurn === match?.turns.length - 1}>
                                <ArrowForwardIosIcon />
                            </Button>
                        </Box>
                    </Paper>
                </Grid>

                {/* Chat interface */}
                <Grid item xs={12} md={6} order={{ xs: 2, md: 1 }}>
                    <Box sx={{ overflowY: 'auto', maxHeight: { xs: 'auto', md: 'calc(100vh - 32px)' } }}>
                        <Typography variant="h4" gutterBottom>
                            {match?.models[0]} vs {match?.models[1]}
                        </Typography>
                        <Typography variant="h6" gutterBottom>
                            Game: {match?.game}
                        </Typography>
                        <Typography variant="h6" gutterBottom>
                            Result: {match?.result === 0.5 ? 'Draw' : `${match?.models[match?.result]} wins!`}
                        </Typography>
                        <Divider sx={{ my: 2 }} />
                        {match?.turns.map((turn, index) => {
                            if (turn.context.message) {
                                return (
                                    <Box
                                        key={index}
                                        sx={{
                                            display: 'flex',
                                            justifyContent: "center",
                                            mb: 2
                                        }}
                                    >
                                        <Paper
                                            sx={{
                                                p: 1,
                                                maxWidth: '70%',
                                                bgcolor: "info.light"
                                            }}
                                        >
                                            <Typography variant="body2" fontWeight="bold">
                                                {turn.context.message}
                                            </Typography>
                                        </Paper>
                                    </Box>
                                );
                            }
                            return (
                                <Box
                                    key={index}
                                    sx={{
                                        display: 'flex',
                                        justifyContent: turn.context.history.length % 2 === 0 ? 'flex-start' : 'flex-end',
                                        mb: 2
                                    }}
                                >
                                    <Paper
                                        sx={{
                                            p: 1,
                                            maxWidth: '70%',
                                            bgcolor: turn.context.history.length % 2 === 0 ? 'primary.light' : 'secondary.light'
                                        }}
                                    >
                                        {Object.entries(turn.context.last_trace || {}).map(([key, value], i, arr) => (
                                            <React.Fragment key={key}>
                                                <Typography variant="body2" fontWeight="bold">
                                                    {key}:
                                                </Typography>
                                                <Typography variant="body2" paragraph>
                                                    {value}
                                                </Typography>
                                                {i < arr.length - 1 && <Divider sx={{ my: 1 }} />}
                                            </React.Fragment>
                                        ))}
                                    </Paper>
                                </Box>
                            );
                        })}
                    </Box>
                </Grid>
            </Grid>
        </Box>
    );
};

export default MatchPage;