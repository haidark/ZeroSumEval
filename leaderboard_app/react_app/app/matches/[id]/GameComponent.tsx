import React from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { Box, Typography } from '@mui/material';

interface GameComponentProps {
  turn: {
    fen: string;
    moveNumber: number;
    lastMove: string;
  };
}

const GameComponent: React.FC<GameComponentProps> = ({ turn }) => {
  const chess = new Chess(turn.fen);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Typography variant="h6" gutterBottom>
        Move {turn.moveNumber}: {turn.lastMove}
      </Typography>
      <Box sx={{ width: '80%', maxWidth: '400px' }}>
        <Chessboard 
          position={turn.fen} 
        //   boardWidth={400}
        //   areArrowsAllowed={false}
        //   boardOrientation={turn.moveNumber % 2 === 0 ? 'white' : 'black'}
        />
      </Box>
      <Typography variant="body2" sx={{ mt: 2 }}>
        {chess.isCheckmate() ? 'Checkmate!' : 
         chess.isCheck() ? 'Check!' : 
         chess.isDraw() ? 'Draw!' : ''}
      </Typography>
    </Box>
  );
};

export default GameComponent;