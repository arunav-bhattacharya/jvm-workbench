package workbench.jmm.l06;

import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.util.concurrent.atomic.AtomicLong;

/**
 * One producer hands transfers to one consumer through a one-item slot, for three seconds.
 * The argument picks the slot: plain (ordinary field access), opaque, or release (the default).
 */
public class HandoffDemo {
    static final class Transfer { long id; long amountCents; }   // plain fields on purpose

    interface Slot {
        boolean offer(Transfer t);   // producer only: false if the slot is still full
        Transfer poll();             // consumer only: null if the slot is empty
    }

    static class Box { Transfer item; }   // null means empty

    static final VarHandle ITEM;
    static {
        try {
            ITEM = MethodHandles.lookup().findVarHandle(Box.class, "item", Transfer.class);
        } catch (ReflectiveOperationException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    static final class PlainSlot extends Box implements Slot {   // what ordinary Java code does
        public boolean offer(Transfer t) {
            if (item != null) return false;
            item = t;
            return true;
        }
        public Transfer poll() {
            Transfer t = item;
            if (t != null) item = null;
            return t;
        }
    }

    static final class OpaqueSlot extends Box implements Slot {
        public boolean offer(Transfer t) {
            if (ITEM.getOpaque(this) != null) return false;
            ITEM.setOpaque(this, t);
            return true;
        }
        public Transfer poll() {
            Transfer t = (Transfer) ITEM.getOpaque(this);
            if (t != null) ITEM.setOpaque(this, null);
            return t;
        }
    }

    static final class ReleaseAcquireSlot extends Box implements Slot {
        public boolean offer(Transfer t) {
            if (ITEM.getAcquire(this) != null) return false;
            ITEM.setRelease(this, t);                         // release: t's fields were written before this
            return true;
        }
        public Transfer poll() {
            Transfer t = (Transfer) ITEM.getAcquire(this);   // acquire: so the consumer sees them
            if (t != null) ITEM.setRelease(this, null);
            return t;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        String mode = args.length > 0 ? args[0] : "release";
        Slot slot = switch (mode) {
            case "plain" -> new PlainSlot();
            case "opaque" -> new OpaqueSlot();
            default -> new ReleaseAcquireSlot();
        };
        AtomicLong handed = new AtomicLong();   // progress, for main to watch
        AtomicLong wrong = new AtomicLong();

        Thread producer = new Thread(() -> {
            for (long id = 1; ; id++) {
                Transfer t = new Transfer();
                t.id = id;                                // 1. fill in the message with plain writes
                t.amountCents = id * 7;
                while (!slot.offer(t)) { }                // 2. spin until the slot is empty, then hand it over
            }
        });
        Thread consumer = new Thread(() -> {
            for (long expected = 1; ; expected++) {
                Transfer t = slot.poll();
                while (t == null) t = slot.poll();        // 3. spin until the slot is full
                if (t.id != expected || t.amountCents != expected * 7) wrong.incrementAndGet();
                handed.set(expected);
            }
        });
        producer.setDaemon(true);   // so the JVM can exit even if they spin forever
        consumer.setDaemon(true);
        producer.start();
        consumer.start();

        long last = -1;
        for (int tick = 0; tick < 4; tick++) {
            Thread.sleep(750);
            long now = handed.get();
            if (now == last) {
                System.out.printf("%s: stuck after %,d handoffs. A spinning thread stopped seeing the slot change.%n", mode, now);
                return;
            }
            last = now;
        }
        System.out.printf("%s: %,d transfers handed over in 3 s, %,d with wrong fields%n", mode, handed.get(), wrong.get());
    }
}
