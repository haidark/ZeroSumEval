"use client"
import React, { useState, useMemo } from 'react';
import { 
    Typography, 
    Paper, 
    Box,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Button,
    Chip,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    TextField
} from '@mui/material';

// Mock data (replace with actual data fetching)
const mockMatches = [
    { id: 1, game: "Chess", model1: "Model A", model2: "Model B", result: "win", model1OldElo: 1500, model1NewElo: 1515, model1EloDelta: 15, model2OldElo: 1520, model2NewElo: 1505, model2EloDelta: -15, date: "2024-08-01" },
    { id: 2, game: "Go", model1: "Model C", model2: "Model D", result: "loss", model1OldElo: 1600, model1NewElo: 1588, model1EloDelta: -12, model2OldElo: 1580, model2NewElo: 1592, model2EloDelta: 12, date: "2024-08-02" },
    { id: 3, game: "Checkers", model1: "Model A", model2: "Model E", result: "draw", model1OldElo: 1550, model1NewElo: 1550, model1EloDelta: 0, model2OldElo: 1540, model2NewElo: 1540, model2EloDelta: 0, date: "2024-08-03" },
    { id: 4, game: "Chess", model1: "Model B", model2: "Model E", result: "win", model1OldElo: 1515, model1NewElo: 1523, model1EloDelta: 8, model2OldElo: 1530, model2NewElo: 1522, model2EloDelta: -8, date: "2024-08-04" },
    { id: 5, game: "Connect 4", model1: "Model D", model2: "Model C", result: "loss", model1OldElo: 1700, model1NewElo: 1690, model1EloDelta: -10, model2OldElo: 1680, model2NewElo: 1690, model2EloDelta: 10, date: "2024-08-05" },
];

const getResultColor = (result) => {
    switch(result) {
        case 'win': return 'success';
        case 'loss': return 'error';
        case 'draw': return 'warning';
        default: return 'default';
    }
};

export default function AllMatchesPage() {
    const [gameFilter, setGameFilter] = useState('');
    const [resultFilter, setResultFilter] = useState('');
    const [model1Filter, setModel1Filter] = useState('');
    const [model2Filter, setModel2Filter] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const filteredMatches = useMemo(() => {
        return mockMatches.filter(match => 
            (gameFilter === '' || match.game === gameFilter) &&
            (resultFilter === '' || match.result === resultFilter) &&
            (model1Filter === '' || match.model1 === model1Filter || match.model2 === model1Filter) &&
            (model2Filter === '' || match.model2 === model2Filter || match.model1 === model2Filter) &&
            (startDate === '' || match.date >= startDate) &&
            (endDate === '' || match.date <= endDate)
        );
    }, [gameFilter, resultFilter, model1Filter, model2Filter, startDate, endDate]);

    const uniqueGames = useMemo(() => [...new Set(mockMatches.map(match => match.game))], []);
    const uniqueModels = useMemo(() => [...new Set([...mockMatches.map(match => match.model1), ...mockMatches.map(match => match.model2)])], []);

    return (
        <Box sx={{ margin: 'auto', mt: 4 }}>
            <Typography variant="h4" gutterBottom>
                All Matches
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                <FormControl sx={{ minWidth: 120 }}>
                    <InputLabel>Game</InputLabel>
                    <Select
                        value={gameFilter}
                        label="Game"
                        onChange={(e) => setGameFilter(e.target.value)}
                    >
                        <MenuItem value="">All</MenuItem>
                        {uniqueGames.map(game => (
                            <MenuItem key={game} value={game}>{game}</MenuItem>
                        ))}
                    </Select>
                </FormControl>

                <FormControl sx={{ minWidth: 120 }}>
                    <InputLabel>Result</InputLabel>
                    <Select
                        value={resultFilter}
                        label="Result"
                        onChange={(e) => setResultFilter(e.target.value)}
                    >
                        <MenuItem value="">All</MenuItem>
                        <MenuItem value="win">Win</MenuItem>
                        <MenuItem value="loss">Loss</MenuItem>
                        <MenuItem value="draw">Draw</MenuItem>
                    </Select>
                </FormControl>

                <FormControl sx={{ minWidth: 120 }}>
                    <InputLabel>Model 1</InputLabel>
                    <Select
                        value={model1Filter}
                        label="Model 1"
                        onChange={(e) => setModel1Filter(e.target.value)}
                    >
                        <MenuItem value="">All</MenuItem>
                        {uniqueModels.map(model => (
                            <MenuItem key={model} value={model}>{model}</MenuItem>
                        ))}
                    </Select>
                </FormControl>

                <FormControl sx={{ minWidth: 120 }}>
                    <InputLabel>Model 2</InputLabel>
                    <Select
                        value={model2Filter}
                        label="Model 2"
                        onChange={(e) => setModel2Filter(e.target.value)}
                    >
                        <MenuItem value="">All</MenuItem>
                        {uniqueModels.map(model => (
                            <MenuItem key={model} value={model}>{model}</MenuItem>
                        ))}
                    </Select>
                </FormControl>

                <TextField
                    label="Start Date"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                />

                <TextField
                    label="End Date"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                />
            </Box>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Game</TableCell>
                            <TableCell>Model 1</TableCell>
                            <TableCell>Model 2</TableCell>
                            <TableCell>Result</TableCell>
                            <TableCell>Model 1 Old ELO</TableCell>
                            <TableCell>Model 1 New ELO</TableCell>
                            <TableCell>Model 1 ELO Δ</TableCell>
                            <TableCell>Model 2 Old ELO</TableCell>
                            <TableCell>Model 2 New ELO</TableCell>
                            <TableCell>Model 2 ELO Δ</TableCell>
                            <TableCell>Date</TableCell>
                            <TableCell>Action</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filteredMatches.map((match) => (
                            <TableRow key={match.id}>
                                <TableCell>{match.game}</TableCell>
                                <TableCell>{match.model1}</TableCell>
                                <TableCell>{match.model2}</TableCell>
                                <TableCell>
                                    <Chip 
                                        label={match.result.toUpperCase()} 
                                        color={getResultColor(match.result)}
                                        size="small"
                                    />
                                </TableCell>
                                <TableCell>{match.model1OldElo}</TableCell>
                                <TableCell>{match.model1NewElo}</TableCell>
                                <TableCell>
                                    <Typography
                                        component="span"
                                        color={match.model1EloDelta > 0 ? "success.main" : (match.model1EloDelta < 0 ? "error.main" : "text.primary")}
                                    >
                                        {match.model1EloDelta > 0 ? '+' : ''}{match.model1EloDelta}
                                    </Typography>
                                </TableCell>
                                <TableCell>{match.model2OldElo}</TableCell>
                                <TableCell>{match.model2NewElo}</TableCell>
                                <TableCell>
                                    <Typography
                                        component="span"
                                        color={match.model2EloDelta > 0 ? "success.main" : (match.model2EloDelta < 0 ? "error.main" : "text.primary")}
                                    >
                                        {match.model2EloDelta > 0 ? '+' : ''}{match.model2EloDelta}
                                    </Typography>
                                </TableCell>
                                <TableCell>{match.date}</TableCell>
                                <TableCell>
                                    <Button variant="contained" size="small" href={`/matches/${match.id}`}>
                                        View Match
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
}