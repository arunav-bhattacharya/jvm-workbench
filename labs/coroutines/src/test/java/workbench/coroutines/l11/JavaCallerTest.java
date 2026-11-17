package workbench.coroutines.l11;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/** The kitchen door seen from plain Java: no Continuation, no Kotlin types beyond the data classes. */
class JavaCallerTest {
    @Test
    @DisplayName("a Java caller chains on cookAsync like on any CompletableFuture")
    void javaCallerChains() throws Exception {
        try (KitchenDoor door = JavaFixtures.servingDoor()) {
            CompletableFuture<String> reply = door.cookAsync(new Order("soup", 4))
                .orTimeout(5, TimeUnit.SECONDS)
                .thenApply(outcome -> "soup: " + outcome);
            assertThat(reply.get()).isEqualTo("soup: SERVED");
        }
    }
}
