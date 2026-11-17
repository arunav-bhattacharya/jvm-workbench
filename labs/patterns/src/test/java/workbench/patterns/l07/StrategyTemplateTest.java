package workbench.patterns.l07;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.patterns.l07.DeliveryPrices.Quote;
import workbench.patterns.l07.Outbound.CallRecord;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.function.LongSupplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class StrategyTemplateTest {

    // ---- strategy: the pricer refactor, pinned to the legacy behavior ----

    private static final int[] WEIGHTS = {0, 1, 999, 2_500, 4_999, 5_000};
    private static final String[] DISTRICTS = {"Old Town", "Hilltop", "Riverside"};

    @Test
    @DisplayName("The strategy map has an entry for every delivery method")
    void mapCoversEveryMethod() {
        assertThat(DeliveryPrices.strategies().keySet()).containsExactlyInAnyOrderElementsOf(EnumSet.allOf(DeliveryMethod.class));
    }

    @Test
    @DisplayName("2.5 kg in the Old Town: bike 2.75, van 4.50, pickup free, in both refactors")
    void fixedPoints() {
        assertThat(DeliveryPrices.priceByMap(new Parcel(DeliveryMethod.BIKE, 2_500, "Old Town"))).isEqualTo(275);
        assertThat(DeliveryPrices.priceByMap(new Parcel(DeliveryMethod.VAN, 2_500, "Old Town"))).isEqualTo(450);
        assertThat(DeliveryPrices.priceByMap(new Parcel(DeliveryMethod.PICKUP, 2_500, "Old Town"))).isEqualTo(0);
        assertThat(DeliveryPrices.priceBySwitch(new Parcel(DeliveryMethod.BIKE, 2_500, "Old Town"))).isEqualTo(275);
        assertThat(DeliveryPrices.priceBySwitch(new Parcel(DeliveryMethod.VAN, 2_500, "Old Town"))).isEqualTo(450);
        assertThat(DeliveryPrices.priceBySwitch(new Parcel(DeliveryMethod.PICKUP, 2_500, "Old Town"))).isEqualTo(0);
    }

    @Test
    @DisplayName("A bike outside the Old Town pays 0.10 more per kg; vans and pickup don't care where")
    void outsideTheOldTown() {
        assertThat(DeliveryPrices.priceBySwitch(new Parcel(DeliveryMethod.BIKE, 2_500, "Hilltop"))).isEqualTo(300);
        assertThat(DeliveryPrices.priceByMap(new Parcel(DeliveryMethod.BIKE, 2_500, "Hilltop"))).isEqualTo(300);
        assertThat(DeliveryPrices.priceByMap(new Parcel(DeliveryMethod.VAN, 2_500, "Riverside"))).isEqualTo(450);
    }

    @Test
    @DisplayName("Both refactors agree with the legacy pricer on every method, weight and district")
    void parityWithLegacy() {
        for (DeliveryMethod m : DeliveryMethod.values()) {
            for (int grams : WEIGHTS) {
                for (String district : DISTRICTS) {
                    Parcel p = new Parcel(m, grams, district);
                    long expected = LegacyPricer.priceCents(p);
                    assertThat(DeliveryPrices.priceByMap(p)).as("map: %s", p).isEqualTo(expected);
                    assertThat(DeliveryPrices.priceBySwitch(p)).as("switch: %s", p).isEqualTo(expected);
                }
            }
        }
    }

    @Test
    @DisplayName("Couriers are asked cheapest first, then fastest, then by name")
    void cheapestThenFastest() {
        List<Quote> quotes = new ArrayList<>(List.of(
                new Quote("Pedal Post", 450, 30),
                new Quote("Big Blue Vans", 350, 90),
                new Quote("Kestrel", 450, 20),
                new Quote("Gull Express", 450, 20)));
        quotes.sort(DeliveryPrices.cheapestThenFastest());
        assertThat(quotes).extracting(Quote::courier).containsExactly("Big Blue Vans", "Gull Express", "Kestrel", "Pedal Post");
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
        String ref = Outbound.timed("courier.book", ticking(), log, () -> "PP-1250");
        assertThat(ref).isEqualTo("PP-1250");
        assertThat(log).containsExactly(new CallRecord("courier.book", 5_000_000, "ok"));
    }

    @Test
    @DisplayName("timed records the exception's simple name and rethrows the same exception")
    void timedFailure() {
        List<CallRecord> log = new ArrayList<>();
        IllegalStateException busy = new IllegalStateException("line busy");
        assertThatThrownBy(() -> Outbound.timed("courier.cancel", ticking(), log, () -> { throw busy; }))
                .isSameAs(busy);
        assertThat(log).containsExactly(new CallRecord("courier.cancel", 5_000_000, "IllegalStateException"));
    }

    @Test
    @DisplayName("timed and the Template Method version log the same record for the same call")
    void sameAsTemplate() {
        List<CallRecord> viaFunction = new ArrayList<>();
        List<CallRecord> viaTemplate = new ArrayList<>();
        Outbound.timed("courier.track", ticking(), viaFunction, () -> "out for delivery");
        new Outbound.OutboundCall<String>(ticking(), viaTemplate) {
            @Override protected String name() { return "courier.track"; }
            @Override protected String doCall() { return "out for delivery"; }
        }.execute();
        assertThat(viaFunction).isEqualTo(viaTemplate).hasSize(1);
    }
}
