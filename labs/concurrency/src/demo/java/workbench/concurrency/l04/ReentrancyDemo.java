package workbench.concurrency.l04;

/** A synchronized method calls another synchronized method on the same object. */
public class ReentrancyDemo {
    static class Account {
        private long balanceCents = 10_000;

        public synchronized void withdraw(long cents) {
            System.out.println("withdraw: holds the lock? " + Thread.holdsLock(this));
            if (canCover(cents)) balanceCents -= cents;      // takes the same lock again
        }

        public synchronized boolean canCover(long cents) {
            System.out.println("canCover: holds the lock? " + Thread.holdsLock(this));
            return balanceCents >= cents;
        }
    }

    static class AuditedAccount extends Account {
        @Override
        public synchronized void withdraw(long cents) {
            System.out.println("audit: about to withdraw " + cents);
            super.withdraw(cents);                           // and again, through super
        }
    }

    public static void main(String[] args) {
        new AuditedAccount().withdraw(2_500);
        System.out.println("done: no thread waited for a lock it already held");
    }
}
