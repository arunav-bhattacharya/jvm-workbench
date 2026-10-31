package workbench.jmm.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;

class VisibilityTest {
    // Long enough for the JIT to compile a spinning loop. With a plain field, a compiled loop never stops.
    private static final long LET_THE_JIT_COMPILE_MS = 300;
    // A generous bound. A correct loop notices the change in microseconds.
    private static final long GENEROUS_JOIN_MS = 5_000;

    private static Thread startDaemon(Runnable r, String name) {
        Thread t = new Thread(r, name);
        t.setDaemon(true);   // a stuck spinner must not keep the test JVM alive
        t.start();
        return t;
    }

    @Test
    @DisplayName("SettlementLoop stops after stop(), even once the JIT has compiled the loop")
    void loopStops() throws InterruptedException {
        for (int round = 1; round <= 3; round++) {
            SettlementLoop loop = new SettlementLoop();
            Thread t = startDaemon(loop, "settlement-" + round);
            Thread.sleep(LET_THE_JIT_COMPILE_MS);
            loop.stop();
            t.join(GENEROUS_JOIN_MS);
            assertThat(t.isAlive())
                    .as("round %d: the loop thread is still spinning after stop(). Can it see the write?", round)
                    .isFalse();
            assertThat(loop.passes()).as("passes after join").isPositive();
        }
    }

    @Test
    @DisplayName("FxRateBoard.awaitRates() returns the published map to a reader that was already waiting")
    void waitingReaderSeesRates() throws InterruptedException {
        Map<String, Long> today = Map.of("EURUSD", 1_084_200L, "GBPUSD", 1_268_900L, "USDJPY", 149_310_000L);
        for (int round = 1; round <= 3; round++) {
            FxRateBoard board = new FxRateBoard();
            AtomicReference<Map<String, Long>> seen = new AtomicReference<>();
            Thread reader = startDaemon(() -> seen.set(board.awaitRates()), "reader-" + round);
            Thread.sleep(LET_THE_JIT_COMPILE_MS);
            board.publish(today);
            reader.join(GENEROUS_JOIN_MS);
            assertThat(reader.isAlive())
                    .as("round %d: the reader is still waiting after publish(). Which field does it spin on?", round)
                    .isFalse();
            assertThat(seen.get()).isEqualTo(today);
        }
    }

    @Test
    @DisplayName("FxRateBoard.awaitRates() returns at once when the rates are already published")
    void publishedFirst() {
        FxRateBoard board = new FxRateBoard();
        board.publish(Map.of("EURUSD", 1_084_200L));
        assertThat(board.awaitRates()).containsEntry("EURUSD", 1_084_200L);
    }
}
