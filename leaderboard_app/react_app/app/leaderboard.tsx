"use client";

import React, { useEffect, useState } from 'react';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Link from 'next/link';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import Modal from '@mui/material/Modal';
import CircularProgress from '@mui/material/CircularProgress';


// Add more games here as needed

function getRandomElo() {
    return Math.floor(Math.random() * 1000) + 1000;
}


export default function Leaderboard(): JSX.Element {
    const [chosenGames, setChosenGames] = useState<string[]>([]);
    const [games, setGames] = useState<string[]>([]);
    const [leaderboard, setLeaderboard] = useState<{ id: string, elo: number }[]>([]);
    const [leaderboards, setLeaderboards] = useState<{ [game: string]: { id: string, elo: number }[] }>({});
    const [searchTerm, setSearchTerm] = useState('');
    const [isLoading, setIsLoading] = useState(true);

    const calculateLeaderboard = () => {
        const newLeaderboard = [];
        const elos: { [key: string]: number[] } = {}
        for (const game of chosenGames) {
            for (const model of leaderboards[game]) {
                if (elos[model.id]) {
                    elos[model.id].push(model.elo);
                } else {
                    elos[model.id] = [model.elo];
                }
            }
        }
        for (const modelId in elos) {
            const elosSum = elos[modelId].reduce((a, b) => a + b, 0);
            const elosAvg = elosSum / elos[modelId].length;
            newLeaderboard.push({ id: modelId, elo: Math.round(elosAvg) });
        }
        return newLeaderboard;
    };

    useEffect(() => {
        const fetchLeaderboard = async () => {
            setIsLoading(true);
            let response = await fetch(`/api/leaderboard`);
            let data: { [game: string]: { model: string, elo: number, wins: number, draws: number, losses: number }[] } = await response.json();
            // convert response data to the format { game: { id: string, elo: number } }
            console.log(data)
            let formattedData: { [game: string]: { id: string, elo: number }[] } = {};
            let games: string[] = [];
            for (const game in data) {
                formattedData[game] = data[game].map(model => ({ id: model.model, elo: model.elo }));
                games.push(game);
            }
            setLeaderboards(formattedData);
            setGames(games);
            setChosenGames(games);
            const newLeaderboard = calculateLeaderboard();
            setLeaderboard(newLeaderboard);

            setIsLoading(false);
        }

        fetchLeaderboard();
    }, []);

    useEffect(() => {
        const newLeaderboard = calculateLeaderboard();
        setLeaderboard(newLeaderboard);
    }, [chosenGames]);

    const handleGameToggle = (game: string) => {
        setChosenGames(prev =>
            prev.includes(game) ? prev.filter(g => g !== game) : [...prev, game]
        );
    };

    const filteredGames = games.filter(game =>
        game.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <>
            <Modal
                open={isLoading}
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
                    <CircularProgress />
                    <Typography id="loading-modal-title" variant="h6" component="h2" sx={{ mt: 2 }}>
                        Loading Leaderboard
                    </Typography>
                </Box>
            </Modal>

            <Accordion>
                <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="panel1a-content"
                    id="panel1a-header"
                >
                    <Typography>Select Games</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <Box mb={2}>
                        <TextField
                            fullWidth
                            label="Search games"
                            variant="outlined"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </Box>
                    <Box sx={{ maxHeight: '300px', overflowY: 'auto' }}>
                        <FormGroup>
                            {filteredGames.map((game) => (
                                <FormControlLabel
                                    key={game}
                                    control={
                                        <Checkbox
                                            checked={chosenGames.includes(game)}
                                            onChange={() => handleGameToggle(game)}
                                            name={game}
                                        />
                                    }
                                    label={game}
                                />
                            ))}
                        </FormGroup>
                    </Box>
                </AccordionDetails>
            </Accordion>
            <TableContainer sx={{ paddingTop: 2 }} component={Paper}>
                <Table aria-label="leaderboard table" sx={{ '& .MuiTableCell-root': { borderRight: '1px solid rgba(224, 224, 224, 1)' } }}>
                    <TableHead>
                        <TableRow>
                            <TableCell style={{ width: '1%', whiteSpace: 'nowrap' }}>Rank</TableCell>
                            <TableCell>Model</TableCell>
                            <TableCell align="right">Agg. ELO</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {leaderboard.sort((a, b) => b.elo - a.elo).map((model, index) => (
                            <TableRow key={index}>
                                <TableCell style={{ width: '1%', whiteSpace: 'nowrap' }}>{index + 1}</TableCell>
                                <TableCell component="th" scope="row">
                                    <Link href={`/models/${model.id}`}>{model.id}</Link>
                                </TableCell>
                                <TableCell style={{ width: '2%', whiteSpace: 'nowrap' }} align="right">{model.elo}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </>
    );
}