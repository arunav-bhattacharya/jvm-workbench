package workbench.coroutines.l11;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/** The facade seen from plain Java: no Continuation, no Kotlin types beyond the data classes. */
class JavaCallerTest {
    @Test
    @DisplayName("a Java caller chains on authorizeAsync like on any CompletableFuture")
    void javaCallerChains() throws Exception {
        try (AuthorizationFacade facade = JavaFixtures.approvingFacade()) {
            CompletableFuture<String> reply = facade.authorizeAsync(new AuthRequest("pay-9", 990))
                .orTimeout(5, TimeUnit.SECONDS)
                .thenApply(decision -> "pay-9: " + decision);
            assertThat(reply.get()).isEqualTo("pay-9: APPROVED");
        }
    }
}
