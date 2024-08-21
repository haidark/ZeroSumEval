import React from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { Box, Typography } from '@mui/material';

interface GameComponentProps {
  turn: any;
  lastMove: boolean | undefined;
  moveNumber: number;
}

const GameComponent: React.FC<GameComponentProps> = ({ turn, lastMove, moveNumber }) => {
  const chess = new Chess(turn.environment.fen);
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Typography variant="h6" gutterBottom>
        Move {moveNumber}: {lastMove}
      </Typography>
      <Box sx={{ width: '80%', maxWidth: '400px' }}>
        <Chessboard
          position={turn.environment.fen}
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