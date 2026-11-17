package workbench.bytecode.l04;

/** Receives one record per proxied call: e.g. {@code "SeatDesk.hold", 3, 5_000_000, false}. */
@FunctionalInterface
public interface CallRecorder {
    void record(String method, int attempts, long nanos, boolean failed);
}
