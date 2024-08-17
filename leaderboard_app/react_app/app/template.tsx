import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';

const Template: React.FC = ({ children }) => {
    return (
        <>
            <Container>
                <Box sx={{ paddingTop: 1, paddingBottom: 1 }}>
                    {children}
                </Box>
            </Container>
        </>
    );
};

export default Template;