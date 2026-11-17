package workbench.patterns.l08;

import java.util.ArrayDeque;
import java.util.Deque;

/** Commands as records, an undo log, and the one rule that keeps undo honest. */
public class UndoDemo {
    static final class Shelf { int units; }

    sealed interface Command permits Restock, Sell {
        void apply(Shelf s);
        void undo(Shelf s);
    }

    record Restock(int units) implements Command {
        public void apply(Shelf s) { s.units += units; }
        public void undo(Shelf s) { s.units -= units; }
    }

    record Sell(int units) implements Command {
        public void apply(Shelf s) {
            if (s.units < units) throw new IllegalStateException("not enough on the shelf");
            s.units -= units;
        }
        public void undo(Shelf s) { s.units += units; }
    }

    static final class CommandLog {
        final Deque<Command> history = new ArrayDeque<>();

        void run(Command c, Shelf s) {
            c.apply(s);              // 1. apply first
            history.push(c);         // 2. record only after it worked
        }

        void undoLast(Shelf s) {
            Command c = history.poll();
            if (c != null) c.undo(s);
        }
    }

    public static void main(String[] args) {
        Shelf rye = new Shelf();
        CommandLog log = new CommandLog();
        log.run(new Restock(12), rye);
        log.run(new Sell(5), rye);
        try {
            log.run(new Sell(40), rye);
        } catch (IllegalStateException e) {
            System.out.println("rejected: " + e.getMessage());
        }
        System.out.println("units " + rye.units + ", history " + log.history);
        log.undoLast(rye);
        System.out.println("after one undo: units " + rye.units + ", history " + log.history);
    }
}
