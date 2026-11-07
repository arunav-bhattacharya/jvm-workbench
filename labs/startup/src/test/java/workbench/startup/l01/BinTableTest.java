package workbench.startup.l01;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CopyOnWriteArrayList;

import static org.assertj.core.api.Assertions.assertThat;

class BinTableTest {
    private static final String BIN_TABLE = "workbench.startup.l01.BinTable";

    // a fresh loader per test: each test sees BinTable before anything has initialized it
    private FreshLoader loader;

    @BeforeEach
    void freshClass() {
        InitLog.clear();
        loader = new FreshLoader();
    }

    @Test
    @DisplayName("version() does not build the table")
    void versionIsCheap() throws Exception {
        assertThat(loader.call(BIN_TABLE, "version")).isEqualTo("bins-2026.11");
        assertThat(InitLog.events())
                .as("calling version() must not run build(); move the table behind a holder")
                .isEmpty();
    }

    @Test
    @DisplayName("version() loads BinTable and no other lab class")
    void versionLoadsOnlyBinTable() throws Exception {
        loader.call(BIN_TABLE, "version");
        // class loading is lazy too: a holder nobody has touched is not even loaded
        assertThat(loader.defined()).containsExactly(BIN_TABLE);
    }

    @Test
    @DisplayName("the first issuerOf builds the table, later lookups reuse it")
    void firstLookupBuildsOnce() throws Exception {
        assertThat(InitLog.events()).isEmpty();
        loader.call(BIN_TABLE, "issuerOf", "4123450000001111");
        loader.call(BIN_TABLE, "issuerOf", "5000000000000009");
        loader.call(BIN_TABLE, "version");
        assertThat(InitLog.events()).containsExactly("table-built");
    }

    @Test
    @DisplayName("8 threads doing their first lookup at once still build the table once")
    void concurrentFirstLookupBuildsOnce() throws Exception {
        Class.forName(BIN_TABLE, false, loader);   // load it, but don't initialize it yet
        CountDownLatch ready = new CountDownLatch(8);
        CountDownLatch go = new CountDownLatch(1);
        List<Throwable> failures = new CopyOnWriteArrayList<>();
        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            Thread t = new Thread(() -> {
                ready.countDown();
                try {
                    go.await();
                    loader.call(BIN_TABLE, "issuerOf", "4111110000001111");
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
    @DisplayName("issuerOf finds the issuer by the first six digits")
    void lookupIsCorrect() throws Exception {
        assertThat(loader.call(BIN_TABLE, "issuerOf", "4111110000001111")).isEqualTo("Northwind Bank");
        assertThat(loader.call(BIN_TABLE, "issuerOf", "4123450000001111")).isEqualTo("Contoso Card Services");
        assertThat(loader.call(BIN_TABLE, "issuerOf", "4123460000001111")).isEqualTo("Fabrikam Credit Union");
        assertThat(loader.call(BIN_TABLE, "issuerOf", "9999990000001111")).isEqualTo("unknown");
    }
}
