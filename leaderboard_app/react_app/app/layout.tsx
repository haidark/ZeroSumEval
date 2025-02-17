import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import Link from 'next/link';
import Button from '@mui/material/Button';

const Template: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return (
        <>
            <html lang='en'>
                <body>
                    <Box sx={{ padding: 1 }}>
                        <AppBar position="static">
                            <Toolbar>
                                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                                    <Link href="/" style={{ textDecoration: 'none', color: 'white' }} >Zero Sum Eval</Link>
                                </Typography>
                                <Link href="/" passHref>
                                    <Button sx={{ color: "white" }}>Leaderboard</Button>
                                </Link>
                                <Link href="/matches" passHref>
                                    <Button sx={{ color: "white" }}>All Matches</Button>
                                </Link>
                            </Toolbar>
                        </AppBar>
                        <Container>
                            <Box sx={{ paddingTop: 3, paddingBottom: 3 }}>
                                {children}
                            </Box>
                        </Container>
                    </Box>
                </body>
            </html>
        </>);
};

export default Template;