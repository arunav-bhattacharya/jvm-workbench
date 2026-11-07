package workbench.performance.l02;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class PaymentGuardsTest {
    private static final int MAX_INLINE_SIZE = 35;   // C2's limit at call sites it doesn't consider hot

    @Test
    @DisplayName("requireAmount fits in 35 bytes of bytecode, so C2 can inline it at any call site")
    void requireAmountIsSmall() throws Exception {
        int size = BytecodeSize.of(PaymentGuards.class, "requireAmount", "(J)J");
        assertThat(size).as("bytecode size of requireAmount").isLessThanOrEqualTo(MAX_INLINE_SIZE);
    }

    @Test
    @DisplayName("requireIdempotencyKey fits in 35 bytes of bytecode")
    void requireKeyIsSmall() throws Exception {
        int size = BytecodeSize.of(PaymentGuards.class, "requireIdempotencyKey", "(Ljava/lang/String;)Ljava/lang/String;");
        assertThat(size).as("bytecode size of requireIdempotencyKey").isLessThanOrEqualTo(MAX_INLINE_SIZE);
    }

    @Test
    @DisplayName("requireAmount still returns valid amounts and rejects bad ones with the same message")
    void requireAmountBehaves() {
        assertThat(PaymentGuards.requireAmount(1)).isEqualTo(1);
        assertThat(PaymentGuards.requireAmount(100_000_000)).isEqualTo(100_000_000);
        assertThatThrownBy(() -> PaymentGuards.requireAmount(0))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("amount must be between 1 and 100000000 cents, got 0");
        assertThatThrownBy(() -> PaymentGuards.requireAmount(100_000_001))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("amount must be between 1 and 100000000 cents, got 100000001");
    }

    @Test
    @DisplayName("requireIdempotencyKey still returns valid keys and rejects bad ones with the same message")
    void requireKeyBehaves() {
        assertThat(PaymentGuards.requireIdempotencyKey("k")).isEqualTo("k");
        String max = "a".repeat(64);
        assertThat(PaymentGuards.requireIdempotencyKey(max)).isSameAs(max);
        assertThatThrownBy(() -> PaymentGuards.requireIdempotencyKey(null))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("idempotency key must be 1 to 64 characters, got null");
        assertThatThrownBy(() -> PaymentGuards.requireIdempotencyKey(""))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("idempotency key must be 1 to 64 characters, got 0");
        assertThatThrownBy(() -> PaymentGuards.requireIdempotencyKey("a".repeat(65)))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("idempotency key must be 1 to 64 characters, got 65");
    }
}
