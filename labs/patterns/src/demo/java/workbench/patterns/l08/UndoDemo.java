package workbench.patterns.l08;

import java.util.ArrayDeque;
import java.util.Deque;

/** Commands as records, an undo log, and the one rule that keeps undo honest. */
public class UndoDemo {
    static final class Wallet { long balance; }

    sealed interface Command permits Deposit, Withdraw {
        void apply(Wallet w);
        void undo(Wallet w);
    }

    record Deposit(long amount) implements Command {
        public void apply(Wallet w) { w.balance += amount; }
        public void undo(Wallet w) { w.balance -= amount; }
    }

    record Withdraw(long amount) implements Command {
        public void apply(Wallet w) {
            if (w.balance < amount) throw new IllegalStateException("insufficient funds");
            w.balance -= amount;
        }
        public void undo(Wallet w) { w.balance += amount; }
    }

    static final class CommandLog {
        final Deque<Command> history = new ArrayDeque<>();

        void run(Command c, Wallet w) {
            c.apply(w);              // 1. apply first
            history.push(c);         // 2. record only after it worked
        }

        void undoLast(Wallet w) {
            Command c = history.poll();
            if (c != null) c.undo(w);
        }
    }

    public static void main(String[] args) {
        Wallet wallet = new Wallet();
        CommandLog log = new CommandLog();
        log.run(new Deposit(100), wallet);
        log.run(new Withdraw(30), wallet);
        try {
            log.run(new Withdraw(1_000), wallet);
        } catch (IllegalStateException e) {
            System.out.println("rejected: " + e.getMessage());
        }
        System.out.println("balance " + wallet.balance + ", history " + log.history);
        log.undoLast(wallet);
        System.out.println("after one undo: balance " + wallet.balance + ", history " + log.history);
    }
}
