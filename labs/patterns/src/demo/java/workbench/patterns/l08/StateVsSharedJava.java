// Closest Java equivalent: the JDK's Flow API, where SubmissionPublisher delivers every event, plus a tiny
// "latest value" holder that drops equal values the way Kotlin's StateFlow does. The JDK has no StateFlow.
package workbench.patterns.l08;

import java.util.List;
import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.SubmissionPublisher;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

public class StateVsSharedJava {

    /** Holds one current value and tells observers about changes; equal values are dropped. */
    static final class LatestValue<T> {
        private final List<Consumer<T>> observers = new CopyOnWriteArrayList<>();
        private T value;

        LatestValue(T initial) { value = initial; }

        synchronized void set(T next) {
            if (Objects.equals(value, next)) return;     // StateFlow-style conflation by equals()
            value = next;
            observers.forEach(o -> o.accept(next));
        }

        synchronized void observe(Consumer<T> o) {
            observers.add(o);
            o.accept(value);                             // new observers get the current value first
        }
    }

    public static void main(String[] args) throws Exception {
        LatestValue<String> state = new LatestValue<>("NEW");
        List<String> fromState = new CopyOnWriteArrayList<>();
        state.observe(fromState::add);

        List<String> fromEvents = new CopyOnWriteArrayList<>();
        CompletableFuture<Void> done;
        try (SubmissionPublisher<String> events = new SubmissionPublisher<>()) {
            done = events.consume(fromEvents::add);     // a subscriber that gets every item
            for (String update : List.of("AUTHORIZED", "AUTHORIZED", "CAPTURED")) {
                state.set(update);
                events.submit(update);
            }
        }                                                // close() completes the stream
        done.get(5, TimeUnit.SECONDS);

        System.out.println("state holder saw:    " + fromState);
        System.out.println("event publisher saw: " + fromEvents);
    }
}
