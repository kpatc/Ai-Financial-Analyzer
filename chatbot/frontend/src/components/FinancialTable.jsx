import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  Typography,
} from '@mui/material';

export default function FinancialTable({ data, title, columns }) {
  if (!data || data.length === 0) {
    return null;
  }

  return (
    <Box sx={{ mt: 3 }}>
      {title && (
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, color: '#e0e0e0' }}>
          {title}
        </Typography>
      )}
      <TableContainer component={Paper} sx={{
        bgcolor: '#1a1a2e',
        border: '1px solid #16213e',
        borderRadius: '8px'
      }}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#16213e' }}>
              {columns.map((col, idx) => (
                <TableCell
                  key={idx}
                  sx={{
                    color: '#6366f1',
                    fontWeight: 600,
                    borderColor: '#16213e'
                  }}
                >
                  {col}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row, rowIdx) => (
              <TableRow
                key={rowIdx}
                sx={{
                  '&:hover': { bgcolor: '#16213e' },
                  borderColor: '#16213e'
                }}
              >
                {columns.map((col, colIdx) => {
                  const key = col.toLowerCase().replace(/[()$%\s]/g, '').replace(/[^\w]/g, '');
                  let value = row[col] || row[key] || '';

                  // Format numbers
                  if (typeof value === 'number') {
                    if (col.includes('%')) {
                      value = value.toFixed(1) + '%';
                    } else if (col.includes('$')) {
                      value = '$' + value.toFixed(2) + 'B';
                    } else {
                      value = value.toFixed(2);
                    }
                  }

                  return (
                    <TableCell
                      key={colIdx}
                      sx={{
                        color: '#e0e0e0',
                        borderColor: '#16213e'
                      }}
                    >
                      {value}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
