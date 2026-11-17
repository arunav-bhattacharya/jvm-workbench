package workbench.startup.l01;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CopyOnWriteArrayList;

import static org.assertj.core.api.Assertions.assertThat;

class PostcodeTableTest {
    private static final String TABLE = "workbench.startup.l01.PostcodeTable";

    // a fresh loader per test: each test sees PostcodeTable before anything has initialized it
    private FreshLoader loader;

    @BeforeEach
    void freshClass() {
        InitLog.clear();
        loader = new FreshLoader();
    }

    @Test
    @DisplayName("version() does not build the table")
    void versionIsCheap() throws Exception {
        assertThat(loader.call(TABLE, "version")).isEqualTo("postcodes-2026.11");
        assertThat(InitLog.events())
                .as("calling version() must not run build(); move the table behind a holder")
                .isEmpty();
    }

    @Test
    @DisplayName("version() loads PostcodeTable and no other lab class")
    void versionLoadsOnlyPostcodeTable() throws Exception {
        loader.call(TABLE, "version");
        // class loading is lazy too: a holder nobody has touched is not even loaded
        assertThat(loader.defined()).containsExactly(TABLE);
    }

    @Test
    @DisplayName("the first depotOf builds the table, later lookups reuse it")
    void firstLookupBuildsOnce() throws Exception {
        assertThat(InitLog.events()).isEmpty();
        loader.call(TABLE, "depotOf", "412345");
        loader.call(TABLE, "depotOf", "500000");
        loader.call(TABLE, "version");
        assertThat(InitLog.events()).containsExactly("table-built");
    }

    @Test
    @DisplayName("8 threads doing their first lookup at once still build the table once")
    void concurrentFirstLookupBuildsOnce() throws Exception {
        Class.forName(TABLE, false, loader);   // load it, but don't initialize it yet
        CountDownLatch ready = new CountDownLatch(8);
        CountDownLatch go = new CountDownLatch(1);
        List<Throwable> failures = new CopyOnWriteArrayList<>();
        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            Thread t = new Thread(() -> {
                ready.countDown();
                try {
                    go.await();
                    loader.call(TABLE, "depotOf", "411111");
                } catch (Throwable e) {
                    failures.add(e);
                }
            });
            t.start();
            threads.add(t);
        }
        ready.await();
        go.countDown();
        for (Thread t : threads) {
            t.join();
        }
        assertThat(failures).isEmpty();
        assertThat(InitLog.events()).containsExactly("table-built");
    }

    @Test
    @DisplayName("depotOf finds the depot for a postcode")
    void lookupIsCorrect() throws Exception {
        assertThat(loader.call(TABLE, "depotOf", "411111")).isEqualTo("North depot");
        assertThat(loader.call(TABLE, "depotOf", "412345")).isEqualTo("River depot");
        assertThat(loader.call(TABLE, "depotOf", "412346")).isEqualTo("Hill depot");
        assertThat(loader.call(TABLE, "depotOf", "999999")).isEqualTo("unknown");
    }
}
