"use client"
import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import { 
    Box, 
    Paper, 
    Typography, 
    Button,
    Divider
} from '@mui/material';
import ArrowBackIosNewIcon from '@mui/icons-material/ArrowBackIosNew';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import GameComponent from './GameComponent';  // Make sure to create this file

// Mock data - replace with actual data fetching
const mockMatch = {
    id: 1,
    model1: "Model A",
    model2: "Model B",
    game: "Chess",
    result: "Model A wins",
    conversation: [
        { model: "Model A", message: "Opening move: e4" },
        { model: "Model B", message: "Responding with: e5" },
        { model: "Model A", message: "Knight to f3" },
        // ... more conversation items
    ],
    turns: [
        { fen: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", moveNumber: 0, lastMove: "Starting position" },
        { fen: "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1", moveNumber: 1, lastMove: "e4" },
        { fen: "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2", moveNumber: 2, lastMove: "e5" },
        { fen: "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2", moveNumber: 3, lastMove: "Nf3" },
        // ... more turns
    ]
};

const MatchPage = () => {
    const params = useParams();
    const matchId = params?.id;
    
    // In a real app, you'd fetch the match data based on the matchId
    const match = mockMatch;  

    const [currentTurn, setCurrentTurn] = useState(0);

    const handlePrevTurn = () => {
        setCurrentTurn(prev => Math.max(0, prev - 1));
    };

    const handleNextTurn = () => {
        setCurrentTurn(prev => Math.min(match.turns.length - 1, prev + 1));
    };

    return (
        <Box sx={{ display: 'flex', height: '100vh', p: 2 }}>
            {/* Left side - Chat interface */}
            <Box sx={{ flex: 1, mr: 2, overflowY: 'auto' }}>
                <Typography variant="h4" gutterBottom>
                    {match.model1} vs {match.model2}
                </Typography>
                <Typography variant="h6" gutterBottom>
                    Game: {match.game}
                </Typography>
                <Typography variant="h6" gutterBottom>
                    Result: {match.result}
                </Typography>
                <Divider sx={{ my: 2 }} />
                {match.conversation.map((item, index) => (
                    <Box 
                        key={index} 
                        sx={{ 
                            display: 'flex', 
                            justifyContent: item.model === match.model1 ? 'flex-start' : 'flex-end',
                            mb: 2
                        }}
                    >
                        <Paper 
                            sx={{ 
                                p: 1, 
                                maxWidth: '70%',
                                bgcolor: item.model === match.model1 ? 'primary.light' : 'secondary.light'
                            }}
                        >
                            <Typography variant="body2">{item.message}</Typography>
                        </Paper>
                    </Box>
                ))}
            </Box>

            {/* Right side - Game component and controls */}
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                <Paper sx={{ mb: 2, p: 2 }}>
                    <GameComponent turn={match.turns[currentTurn]} />
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <Button onClick={handlePrevTurn} disabled={currentTurn === 0}>
                        <ArrowBackIosNewIcon />
                    </Button>
                    <Typography sx={{ mx: 2 }}>
                        Turn {currentTurn + 1} of {match.turns.length}
                    </Typography>
                    <Button onClick={handleNextTurn} disabled={currentTurn === match.turns.length - 1}>
                        <ArrowForwardIosIcon />
                    </Button>
                </Box>
                </Paper>
            </Box>
        </Box>
    );
};

export default MatchPage;