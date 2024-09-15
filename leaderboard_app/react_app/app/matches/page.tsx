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
    const [matches, setMatches] = useState<{ id: number, models: string[], game: string, timestamp: string, results: { [model: string]: { elos_delta: number[], result: number } } }[]>([]);
    const [gameFilter, setGameFilter] = useState('');
    const [modelFilter1, setModelFilter1] = useState('');
    const [modelFilter2, setModelFilter2] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [uniqueGames, setUniqueGames] = useState<string[]>([]);
    const [uniqueModels, setUniqueModels] = useState<string[]>([]);

    useEffect(() => {
        // Fetch model matches based on id
        const fetchMatches = async () => {
            const response = await fetch(`/api/matches`);
            const data = await response.json();

            // Update state with fetched data
            setMatches(data);

            // Update unique games and opponents
            setUniqueGames(Array.from(new Set<string>(matches.map(match => match.game))));
            setUniqueModels(Array.from(new Set([...matches.map(match => match.models[0]), ...matches.map(match => match.models[1])])));

        }
        fetchMatches()
    }, []);


    const filteredMatches = useMemo(() => {
        return matches.filter(match =>
            (gameFilter === '' || match.game === gameFilter) &&
            (modelFilter1 === '' || match.models[0] === modelFilter1) &&
            (modelFilter2 === '' || match.models[1] === modelFilter2) &&
            (startDate === '' || match.timestamp >= startDate) &&
            (endDate === '' || match.timestamp <= endDate)
        );
    }, [gameFilter, modelFilter1, modelFilter2, startDate, endDate, matches, uniqueGames, uniqueModels]);


    return (
        <Box sx={{ maxWidth: 1000, margin: 'auto', mt: 4 }}>
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
                    <InputLabel>Model 1</InputLabel>
                    <Select
                        value={modelFilter1}
                        label="Model 1"
                        onChange={(e) => setModelFilter1(e.target.value)}
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
                        value={modelFilter2}
                        label="Model 2"
                        onChange={(e) => setModelFilter2(e.target.value)}
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
                            <TableCell>Model 1 ELO</TableCell>
                            <TableCell>Model 2 ELO</TableCell>
                            <TableCell>Result</TableCell>
                            <TableCell>Date</TableCell>
                            <TableCell>Action</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filteredMatches.map((match, i) => (
                            <TableRow key={i}>
                                <TableCell>{match.game}</TableCell>
                                <TableCell>
                                    <Link href={`/models/${match.models[0]}`}>
                                        {match.models[0]}
                                    </Link>
                                </TableCell>
                                <TableCell>
                                    <Link href={`/models/${match.models[1]}`}>
                                        {match.models[1]}
                                    </Link>
                                </TableCell>
                                <TableCell>
                                    <Typography>
                                        {match.results[match.models[0]].elos_delta[0]}
                                    </Typography>
                                    <Typography color={match.results[match.models[0]].elos_delta[1] - match.results[match.models[0]].elos_delta[0] > 0 ? "green" : "red"}>
                                        ({match.results[match.models[0]].elos_delta[1] - match.results[match.models[0]].elos_delta[0] > 0 ? '+' : ''}{match.results[match.models[0]].elos_delta[1] - match.results[match.models[0]].elos_delta[0]})
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    <Typography>
                                        {match.results[match.models[1]].elos_delta[0]}
                                    </Typography>
                                    <Typography color={match.results[match.models[1]].elos_delta[1] - match.results[match.models[1]].elos_delta[0] > 0 ? "green" : "red"}>
                                        ({match.results[match.models[1]].elos_delta[1] - match.results[match.models[1]].elos_delta[0] > 0 ? '+' : ''}{match.results[match.models[1]].elos_delta[1] - match.results[match.models[1]].elos_delta[0]})
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    {match.results[match.models[0]].result === 0.5 ? 'Draw' : match.results[match.models[0]].result == 1 ? `${match.models[0]} wins!` : `${match.models[1]} wins!`}
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