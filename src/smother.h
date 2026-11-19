/*
  Smothered-mate prover for Stockfish.
  Licensed under the GNU GPL v3 (same as Stockfish).

  Proves, by exhaustive AND/OR search, that the side to move can force a
  smothered mate against every defence. The attacker may play any checking
  move (including sacrifices); the defender may play every legal reply.
  A line only succeeds if it ends in a smothered mate: an ordinary mate is
  treated as a failure, so the result is a guarantee, not a preference.
*/

#ifndef SMOTHER_H_INCLUDED
#define SMOTHER_H_INCLUDED

#include <atomic>
#include <cstdint>
#include <vector>

#include "misc.h"
#include "types.h"

namespace Stockfish {

class Position;

namespace Smother {

// Classic: every square next to the mated king holds one of its own pieces
//          (only a knight, or a pawn promoting to one, can deliver this).
// AnyPiece: every square next to the king holds one of its own pieces,
//           except the square of the checking piece itself.
enum class Style {
    Classic,
    AnyPiece
};

// True if the side to move is checkmated and the mate is smothered.
bool is_smothered_mate(const Position& pos, Style style);

struct Limits {
    int         maxMoves = 8;           // attacker moves (mate in N)
    Style       style    = Style::AnyPiece;
    bool        strict   = false;           // every defence must be smothered
    int         quietMoves = 1;             // non-checking attacker moves per line
    std::uint64_t maxNodes = 5000000;   // 0 = unlimited
    TimePoint   deadline = 0;           // absolute now() value, 0 = none
};

struct Result {
    bool              found   = false;
    bool              aborted = false;
    int               mateIn  = 0;      // attacker moves
    std::uint64_t     nodes   = 0;
    std::vector<Move> pv;               // principal (longest-resistance) line
};

// Search from pos (side to move = attacker). pos is restored on return.
// stop is polled so a GUI "stop" interrupts the proof.
Result prove(Position& pos, const Limits& limits, const std::atomic<bool>& stop);

}  // namespace Smother
}  // namespace Stockfish

#endif  // #ifndef SMOTHER_H_INCLUDED
