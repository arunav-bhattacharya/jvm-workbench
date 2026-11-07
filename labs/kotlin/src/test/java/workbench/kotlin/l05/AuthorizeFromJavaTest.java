package workbench.kotlin.l05;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class AuthorizeFromJavaTest {

    @Test
    @DisplayName("Java passes the context parameters first, then the receiver, then the ordinary arguments")
    void javaSeesLeadingParameters() {
        List<String> lines = new ArrayList<>();
        AuditLog log = lines::add;
        // Kotlin: context(audit: AuditLog, tx: TxContext) fun AuthRequest.authorize(limitMinor: Long)
        // JVM:    static Decision authorize(AuditLog, TxContext, AuthRequest, long)
        Decision d = AuthorizeKt.authorize(log, new TxContext("tx-j"), new AuthRequest(2_500L, "gbp", "tok_1"), 10_000L);
        assertThat(d).isSameAs(Decision.Approved.INSTANCE);
        assertThat(lines).containsExactly("[tx-j] approved 2500 GBP");
    }
}
