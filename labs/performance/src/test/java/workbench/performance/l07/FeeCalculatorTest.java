package workbench.performance.l07;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.lang.management.ManagementFactory;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class FeeCalculatorTest {
    private static final int BUDGET_BYTES_PER_CALL = 100;

    /** A log with DEBUG off, like production. It counts what it receives. */
    static final class QuietLog implements DebugLog {
        int messages;
        public boolean isDebugEnabled() { return false; }
        public void debug(String message) { messages++; }
    }

    /** A log with DEBUG on, which keeps every message. */
    static final class ChattyLog implements DebugLog {
        final List<String> messages = new ArrayList<>();
        public boolean isDebugEnabled() { return true; }
        public void debug(String message) { messages.add(message); }
    }

    private static Payment[] payments(int n) {
        Payment[] ps = new Payment[n];
        for (int i = 0; i < n; i++) {
            ps[i] = new Payment("pay_" + i, i % 2 == 0 ? "EUR" : "USD",
                    (1 + (i * 7_919) % 99_999) + "." + (10 + i % 89), "m_" + (i % 50));
        }
        return ps;
    }

    // the rule written independently of your code: 2.9% + 0.30, half-even to cents
    private static long expectedFee(String amount) {
        return new BigDecimal(amount).multiply(new BigDecimal("0.029")).add(new BigDecimal("0.30"))
                .setScale(2, RoundingMode.HALF_EVEN).unscaledValue().longValueExact();
    }

    @Test
    @DisplayName("fees are unchanged, including amounts that land exactly on half a cent")
    void feesAreCorrect() {
        FeeCalculator calc = new FeeCalculator(new QuietLog());
        List<String> amounts = new ArrayList<>(List.of("5.00", "15.00", "1234.56", "0.01", "99999.99", "100.50"));
        for (Payment p : payments(500)) amounts.add(p.amount());
        for (String amount : amounts) {
            assertThat(calc.feeCents(new Payment("p", "EUR", amount, "m")))
                    .as("fee for %s", amount).isEqualTo(expectedFee(amount));
        }
    }

    @Test
    @DisplayName("currencies that are not three letters A to Z are still rejected")
    void badCurrencyRejected() {
        FeeCalculator calc = new FeeCalculator(new QuietLog());
        for (String bad : new String[] {"eur", "EURO", "E1R", "", "US"}) {
            assertThatThrownBy(() -> calc.feeCents(new Payment("p", bad, "10.00", "m")))
                    .as("currency '%s'", bad)
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessage("bad currency");
        }
    }

    @Test
    @DisplayName("with DEBUG on, the log line is exactly the same as before")
    void debugMessageUnchanged() {
        ChattyLog log = new ChattyLog();
        new FeeCalculator(log).feeCents(new Payment("pay_7", "EUR", "1234.56", "m_3"));
        assertThat(log.messages).containsExactly("payment pay_7 merchant=m_3 amount=1234.56 fee=36.10");
    }

    @Test
    @DisplayName("allocates under 100 bytes per call once warm (measured with the per-thread allocation counter)")
    void allocationBudget() {
        FeeCalculator calc = new FeeCalculator(new QuietLog());
        Payment[] ps = payments(1_024);
        var threads = (com.sun.management.ThreadMXBean) ManagementFactory.getThreadMXBean();
        int calls = 100_000;
        long sink = 0;
        List<Double> rounds = new ArrayList<>();
        // allocation only settles once C2 has compiled feeCents, so measure 10 rounds and judge the best one;
        // a busy machine can delay the compile, but it can't make warm code allocate less than it does
        for (int round = 0; round < 10; round++) {
            long before = threads.getCurrentThreadAllocatedBytes();
            for (int i = 0; i < calls; i++) sink += calc.feeCents(ps[i & 1023]);
            rounds.add((double) (threads.getCurrentThreadAllocatedBytes() - before) / calls);
        }
        double best = rounds.stream().mapToDouble(Double::doubleValue).min().orElseThrow();

        assertThat(sink).isPositive();
        assertThat(best).as("bytes per feeCents call (best of rounds %s)", rounds)
                .isLessThan(BUDGET_BYTES_PER_CALL);
    }
}
