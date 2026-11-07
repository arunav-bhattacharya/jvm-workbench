package workbench.patterns.l07;

import java.util.List;
import java.util.function.LongSupplier;
import java.util.function.Supplier;

/**
 * Every outbound PSP call must be timed and logged the same way. The classic answer is a Template
 * Method base class, {@link OutboundCall} below, which is given and works. Your job is the modern one:
 * an execute-around function that takes the varying step as a lambda.
 */
public final class Outbound {
    private Outbound() {}

    /** One line in the call log. {@code outcome} is "ok", or the simple class name of the exception. */
    public record CallRecord(String name, long nanos, String outcome) {}

    /**
     * Runs {@code body} and ALWAYS adds exactly one {@link CallRecord} to {@code log}: the time between
     * one clock read before and one after, and the outcome. Returns what {@code body} returns.
     * If {@code body} throws, record the exception's simple class name and rethrow the same exception.
     */
    public static <T> T timed(String name, LongSupplier clock, List<CallRecord> log, Supplier<T> body) {
        throw new UnsupportedOperationException("TODO: read the clock, run body in try/catch/finally, record once");
    }

    /** The Template Method version, for comparison. Given; you don't need to change it. */
    public abstract static class OutboundCall<T> {
        private final LongSupplier clock;
        private final List<CallRecord> log;

        protected OutboundCall(LongSupplier clock, List<CallRecord> log) {
            this.clock = clock;
            this.log = log;
        }

        /** The skeleton. final, so subclasses can only fill in the hooks. */
        public final T execute() {
            long start = clock.getAsLong();
            String outcome = "ok";
            try {
                return doCall();
            } catch (RuntimeException e) {
                outcome = e.getClass().getSimpleName();
                throw e;
            } finally {
                log.add(new CallRecord(name(), clock.getAsLong() - start, outcome));
            }
        }

        protected abstract String name();     // hook: what to call it in the log
        protected abstract T doCall();         // hook: the varying step
    }
}
