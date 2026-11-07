package workbench.memory.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.lang.ref.Reference;
import java.lang.ref.ReferenceQueue;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;

class ReachabilityTest {

    @Test
    @DisplayName("close() frees the native memory")
    void closeFrees() {
        NativeMemory memory = new NativeMemory();
        try (NativeBuffer buffer = new NativeBuffer(memory, 4_096)) {
            assertThat(memory.openHandles()).isEqualTo(1);
            assertThat(buffer.handle()).isPositive();
        }
        assertThat(memory.openHandles()).isZero();
        assertThat(memory.frees()).isEqualTo(1);
    }

    @Test
    @DisplayName("closing a buffer twice frees it once")
    void closeTwiceFreesOnce() {
        NativeMemory memory = new NativeMemory();
        NativeBuffer buffer = new NativeBuffer(memory, 4_096);
        buffer.close();
        assertThatCode(buffer::close).as("second close").doesNotThrowAnyException();
        assertThat(memory.frees()).isEqualTo(1);
    }

    @Test
    @DisplayName("a buffer nobody closed is freed by the cleaner once it is unreachable")
    void forgottenBufferIsCleaned() throws Exception {
        NativeMemory memory = new NativeMemory();
        NativeBuffer buffer = new NativeBuffer(memory, 4_096);
        buffer = null;                                           // forget it without closing
        assertThat(GcWait.until(() -> memory.frees() == 1))
                .as("the cleaner freed the forgotten buffer within a few GCs").isTrue();
        assertThat(memory.openHandles()).isZero();
    }

    @Test
    @DisplayName("a closed buffer is not freed again when it is collected")
    void closedBufferIsNotCleanedAgain() throws Exception {
        NativeMemory memory = new NativeMemory();
        NativeBuffer buffer = new NativeBuffer(memory, 4_096);
        buffer.close();
        ReferenceQueue<Object> queue = new ReferenceQueue<>();
        WeakReference<Object> probe = new WeakReference<>(buffer, queue);
        buffer = null;
        assertThat(GcWait.untilEnqueued(queue, probe)).as("the buffer was collected").isTrue();
        Thread.sleep(100);                                       // give the cleaner thread time to (wrongly) run
        assertThat(memory.frees()).isEqualTo(1);
    }

    @Test
    @DisplayName("the registry calls every listener that is still alive")
    void firesLiveListeners() {
        WeakListenerRegistry<Consumer<String>> registry = new WeakListenerRegistry<>();
        List<String> seen = new ArrayList<>();
        Consumer<String> velocity = e -> seen.add("velocity:" + e);
        Consumer<String> geo = e -> seen.add("geo:" + e);
        registry.register(velocity);
        registry.register(geo);
        registry.fire(l -> l.accept("auth-1"));
        assertThat(seen).containsExactly("velocity:auth-1", "geo:auth-1");
        assertThat(registry.size()).isEqualTo(2);
        Reference.reachabilityFence(velocity);
        Reference.reachabilityFence(geo);
    }

    @Test
    @DisplayName("a listener that only the registry refers to disappears after GC")
    void unloadedListenerDisappears() throws Exception {
        WeakListenerRegistry<Consumer<String>> registry = new WeakListenerRegistry<>();
        List<String> seen = new ArrayList<>();
        Consumer<String> rule = e -> seen.add("unloaded rule saw " + e);
        registry.register(rule);
        ReferenceQueue<Object> queue = new ReferenceQueue<>();
        WeakReference<Object> probe = new WeakReference<>(rule, queue);
        rule = null;                                             // the rule is unloaded: nothing else refers to it
        assertThat(GcWait.untilEnqueued(queue, probe)).as("the listener was collected").isTrue();
        assertThat(registry.size()).isZero();
        registry.fire(l -> l.accept("auth-2"));
        assertThat(seen).isEmpty();
    }

    @Test
    @DisplayName("a listener its owner still holds survives GC and keeps firing")
    void heldListenerSurvives() throws Exception {
        WeakListenerRegistry<Consumer<String>> registry = new WeakListenerRegistry<>();
        List<String> seen = new ArrayList<>();
        Consumer<String> rule = e -> seen.add("live rule saw " + e);
        registry.register(rule);
        ReferenceQueue<Object> queue = new ReferenceQueue<>();
        WeakReference<Object> garbage = new WeakReference<>(new Object(), queue);
        assertThat(GcWait.untilEnqueued(queue, garbage)).as("a GC processed weak references").isTrue();
        registry.fire(l -> l.accept("auth-3"));
        assertThat(seen).containsExactly("live rule saw auth-3");
        assertThat(registry.size()).isEqualTo(1);
        Reference.reachabilityFence(rule);                       // keeps `rule` strongly reachable up to here
    }
}
