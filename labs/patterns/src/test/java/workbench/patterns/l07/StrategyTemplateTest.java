package workbench.patterns.l07;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.patterns.l07.Fees.Quote;
import workbench.patterns.l07.Outbound.CallRecord;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.function.LongSupplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class StrategyTemplateTest {

    // ---- strategy: the router refactor, pinned to the legacy behavior ----

    private static final long[] AMOUNTS = {0, 1, 999, 10_000, 123_456, 5_000_000};
    private static final String[] COUNTRIES = {"DE", "FR", "US"};

    @Test
    @DisplayName("The strategy map has an entry for every payment method")
    void mapCoversEveryMethod() {
        assertThat(Fees.strategies().keySet()).containsExactlyInAnyOrderElementsOf(EnumSet.allOf(Method.class));
    }

    @Test
    @DisplayName("100.00 domestic: card 3.20, SEPA 0.25, wallet 1.50, in both refactors")
    void fixedPoints() {
        assertThat(Fees.feeByMap(new Payment(Method.CARD, 10_000, "DE"))).isEqualTo(320);
        assertThat(Fees.feeByMap(new Payment(Method.SEPA, 10_000, "DE"))).isEqualTo(25);
        assertThat(Fees.feeByMap(new Payment(Method.WALLET, 10_000, "DE"))).isEqualTo(150);
        assertThat(Fees.feeBySwitch(new Payment(Method.CARD, 10_000, "DE"))).isEqualTo(320);
        assertThat(Fees.feeBySwitch(new Payment(Method.SEPA, 10_000, "DE"))).isEqualTo(25);
        assertThat(Fees.feeBySwitch(new Payment(Method.WALLET, 10_000, "DE"))).isEqualTo(150);
    }

    @Test
    @DisplayName("A cross-border card pays 1% more; SEPA and wallet don't care about the country")
    void crossBorder() {
        assertThat(Fees.feeBySwitch(new Payment(Method.CARD, 10_000, "FR"))).isEqualTo(420);
        assertThat(Fees.feeByMap(new Payment(Method.CARD, 10_000, "FR"))).isEqualTo(420);
        assertThat(Fees.feeByMap(new Payment(Method.WALLET, 10_000, "US"))).isEqualTo(150);
    }

    @Test
    @DisplayName("Both refactors agree with the legacy router on every method, amount and country")
    void parityWithLegacy() {
        for (Method m : Method.values()) {
            for (long amount : AMOUNTS) {
                for (String country : COUNTRIES) {
                    Payment p = new Payment(m, amount, country);
                    long expected = LegacyRouter.fee(p);
                    assertThat(Fees.feeByMap(p)).as("map: %s", p).isEqualTo(expected);
                    assertThat(Fees.feeBySwitch(p)).as("switch: %s", p).isEqualTo(expected);
                }
            }
        }
    }

    @Test
    @DisplayName("PSPs are tried cheapest first, then fastest, then by name")
    void cheapestThenFastest() {
        List<Quote> quotes = new ArrayList<>(List.of(
                new Quote("Northpay", 30, 200),
                new Quote("Adyx", 25, 900),
                new Quote("Kestrel", 30, 120),
                new Quote("Bluefin", 30, 120)));
        quotes.sort(Fees.cheapestThenFastest());
        assertThat(quotes).extracting(Quote::psp).containsExactly("Adyx", "Bluefin", "Kestrel", "Northpay");
    }

    // ---- template method vs execute around ----

    /** A fake clock: every read moves time forward by 5 ms. */
    private static LongSupplier ticking() {
        long[] now = {0};
        return () -> now[0] += 5_000_000;
    }

    @Test
    @DisplayName("timed returns the body's result and records ok with the time between two clock reads")
    void timedSuccess() {
        List<CallRecord> log = new ArrayList<>();
        String auth = Outbound.timed("psp.authorize", ticking(), log, () -> "A-1250");
        assertThat(auth).isEqualTo("A-1250");
        assertThat(log).containsExactly(new CallRecord("psp.authorize", 5_000_000, "ok"));
    }

    @Test
    @DisplayName("timed records the exception's simple name and rethrows the same exception")
    void timedFailure() {
        List<CallRecord> log = new ArrayList<>();
        IllegalStateException boom = new IllegalStateException("PSP 503");
        assertThatThrownBy(() -> Outbound.timed("psp.capture", ticking(), log, () -> { throw boom; }))
                .isSameAs(boom);
        assertThat(log).containsExactly(new CallRecord("psp.capture", 5_000_000, "IllegalStateException"));
    }

    @Test
    @DisplayName("timed and the Template Method version log the same record for the same call")
    void sameAsTemplate() {
        List<CallRecord> viaFunction = new ArrayList<>();
        List<CallRecord> viaTemplate = new ArrayList<>();
        Outbound.timed("psp.refund", ticking(), viaFunction, () -> 500L);
        new Outbound.OutboundCall<Long>(ticking(), viaTemplate) {
            @Override protected String name() { return "psp.refund"; }
            @Override protected Long doCall() { return 500L; }
        }.execute();
        assertThat(viaFunction).isEqualTo(viaTemplate).hasSize(1);
    }
}
