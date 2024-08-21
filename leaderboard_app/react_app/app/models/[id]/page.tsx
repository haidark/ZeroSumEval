"use client"
import React, { useState, useMemo, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
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

const getResultColor = (result: number) => {
    switch (result) {
        case 1: return 'success';
        case 0: return 'error';
        case 0.5: return 'warning';
        default: return 'default';
    }
};

export default function ModelPage() {
    const params = useParams()
    const model_id: string = params.id;


    const [matches, setMatches] = useState<{ id: number, opponent: string, game: string, timestamp: string, results: { [model: string]: { elos_delta: number[], result: number } } }[]>([]);
    const [gameFilter, setGameFilter] = useState('');
    const [resultFilter, setResultFilter] = useState<number>(-1);
    const [opponentFilter, setOpponentFilter] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [uniqueGames, setUniqueGames] = useState<string[]>([]);
    const [uniqueOpponents, setUniqueOpponents] = useState<string[]>([]);

    useEffect(() => {
        // Fetch model matches based on id
        const fetchMatches = async () => {
            const response = await fetch(`http://localhost:8000/api/models/${model_id}`);
            const data = await response.json();

            // Update state with fetched data
            setMatches(data);

            // Update unique games and opponents
            setUniqueGames([...new Set(data.map(match => match.game))]);
            setUniqueOpponents([...new Set(data.map(match => match.opponent))]);

        }
        fetchMatches()
    }, []);


    const filteredMatches = useMemo(() => {
        return matches.filter(match =>
            (gameFilter === '' || match.game === gameFilter) &&
            (resultFilter === -1 || match.results[model_id].result === resultFilter) &&
            (opponentFilter === '' || match.opponent === opponentFilter) &&
            (startDate === '' || match.timestamp >= startDate) &&
            (endDate === '' || match.timestamp <= endDate)
        );
    }, [gameFilter, resultFilter, opponentFilter, startDate, endDate, matches]);

    const getResultString = (result: number) => {
        if (result === 1) {
            return 'Win';
        } else if (result === 0) {
            return 'Loss';
        } else {
            return 'Draw';
        }
    }

    console.log(matches)

    return (
        <Box sx={{ maxWidth: 1000, margin: 'auto', mt: 4 }}>
            <Typography variant="h4" gutterBottom>
                Model {model_id} Matches
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
                        <MenuItem value={-1}>All</MenuItem>
                        <MenuItem value={1}>Win</MenuItem>
                        <MenuItem value={0}>Loss</MenuItem>
                        <MenuItem value={0.5}>Draw</MenuItem>
                    </Select>
                </FormControl>

                <FormControl sx={{ minWidth: 120 }}>
                    <InputLabel>Opponent</InputLabel>
                    <Select
                        value={opponentFilter}
                        label="Opponent"
                        onChange={(e) => setOpponentFilter(e.target.value)}
                    >
                        <MenuItem value="">All</MenuItem>
                        {uniqueOpponents.map(opponent => (
                            <MenuItem key={opponent} value={opponent}>{opponent}</MenuItem>
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
                            <TableCell>Opponent</TableCell>
                            <TableCell>Result</TableCell>
                            <TableCell>Old ELO</TableCell>
                            <TableCell>New ELO</TableCell>
                            <TableCell>ELO Δ</TableCell>
                            <TableCell>Date</TableCell>
                            <TableCell>Action</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filteredMatches.map((match, i) => (
                            <TableRow key={i}>
                                <TableCell>{match.game}</TableCell>
                                <TableCell>{match.opponent}</TableCell>
                                <TableCell>
                                    <Chip
                                        label={getResultString(match.results[model_id].result).toUpperCase()}
                                        color={getResultColor(match.results[model_id].result) as "success" | "error" | "warning" | "default"}
                                        size="small"
                                    />
                                </TableCell>
                                <TableCell>{match.results[model_id].elos_delta[0]}</TableCell>
                                <TableCell>{match.results[model_id].elos_delta[1]}</TableCell>
                                <TableCell>
                                    <Typography
                                        component="span"
                                        color={match.results[model_id].elos_delta[1] - match.results[model_id].elos_delta[0] > 0 ? "success.main" : (match.results[model_id].elos_delta[1] - match.results[model_id].elos_delta[0] < 0 ? "error.main" : "text.primary")}
                                    >
                                        {match.results[model_id].elos_delta[1] - match.results[model_id].elos_delta[0] > 0 ? '+' : ''}{match.results[model_id].elos_delta[1] - match.results[model_id].elos_delta[0]}
                                    </Typography>
                                </TableCell>
                                <TableCell>{match.timestamp}</TableCell>
                                <TableCell>
                                    <Link href={`/matches/${match.id}`} passHref>
                                        <Button variant="contained" size="small">
                                            View Match
                                        </Button>
                                    </Link>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
}