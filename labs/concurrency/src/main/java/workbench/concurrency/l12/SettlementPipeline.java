package workbench.concurrency.l12;

import java.util.List;
import java.util.function.Consumer;

/**
 * Moves settlement records from producer threads to consumer threads through one bounded queue,
 * then shuts the consumers down with poison pills.
 *
 * <ul>
 *   <li>Start one producer thread per inner list of {@code perProducer}; each puts its records, in order.</li>
 *   <li>Start {@code consumers} consumer threads; each takes records and calls {@code process} on them.</li>
 *   <li>Use an {@link java.util.concurrent.ArrayBlockingQueue} of {@code capacity}.</li>
 *   <li>When ALL producers have finished, put one pill per consumer. A consumer that takes a pill stops.
 *       Compare against the pill with {@code ==}: a real record may contain the same text.</li>
 *   <li>Return the number of records processed, and only after every consumer thread has stopped.</li>
 * </ul>
 */
public final class SettlementPipeline {
    private SettlementPipeline() {}

    public static int run(List<List<String>> perProducer, int consumers, int capacity, Consumer<String> process)
            throws InterruptedException {
        throw new UnsupportedOperationException("TODO: producers put, consumers take until they see a pill, one pill per consumer after the producers finish");
    }
}
