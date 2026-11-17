package workbench.patterns.l05;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.patterns.l05.DeliveryFee.Delivery;

import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeoutException;
import java.util.function.LongSupplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DecoratorProxyTest {

    // ---- decorator chain ----

    private static final DeliveryFee STANDARD =
            DeliveryFee.perKm(50).plusFixed(200).heavySurcharge(5_000, 300).cappedAt(800);

    @Test
    @DisplayName("perKm charges the same amount for every kilometer")
    void perKm() {
        assertThat(DeliveryFee.perKm(50).cents(new Delivery(4, 2_000))).isEqualTo(200);
        assertThat(DeliveryFee.perKm(35).cents(new Delivery(7, 2_000))).isEqualTo(245);
    }

    @Test
    @DisplayName("A light parcel, 4 km: 2.00 to start + 4 x 0.50 = 4.00")
    void light() {
        assertThat(STANDARD.cents(new Delivery(4, 2_000))).isEqualTo(400);
    }

    @Test
    @DisplayName("A heavy parcel, 4 km: 4.00 + 3.00 surcharge = 7.00; exactly 5 kg is not heavy")
    void heavy() {
        assertThat(STANDARD.cents(new Delivery(4, 12_000))).isEqualTo(700);
        assertThat(STANDARD.cents(new Delivery(4, 5_000))).isEqualTo(400);
    }

    @Test
    @DisplayName("A heavy parcel, 20 km, hits the 8.00 cap")
    void capped() {
        assertThat(STANDARD.cents(new Delivery(20, 12_000))).isEqualTo(800);
    }

    @Test
    @DisplayName("Order matters: capping before the surcharge gives 11.00")
    void orderMatters() {
        DeliveryFee capFirst = DeliveryFee.perKm(50).plusFixed(200).cappedAt(800).heavySurcharge(5_000, 300);
        assertThat(capFirst.cents(new Delivery(20, 12_000))).isEqualTo(1_100);
    }

    @Test
    @DisplayName("Each decorator returns a new fee and leaves the one it wraps unchanged")
    void decoratorsDontMutate() {
        DeliveryFee base = DeliveryFee.perKm(50);
        DeliveryFee withFixed = base.plusFixed(200);
        assertThat(base.cents(new Delivery(4, 2_000))).isEqualTo(200);
        assertThat(withFixed.cents(new Delivery(4, 2_000))).isEqualTo(400);
    }

    // ---- timing proxy ----

    public interface CourierBooking {
        String book(String address, int grams) throws TimeoutException;
        String bookTwice(String address, int grams) throws TimeoutException;
    }

    static final class RealCourier implements CourierBooking {
        int calls;
        @Override public String book(String address, int grams) throws TimeoutException {
            calls++;
            if (grams < 0) throw new IllegalArgumentException("negative weight");
            if (address.startsWith("Gull Island")) throw new TimeoutException("the courier took longer than 120 ms");
            return "PP-" + grams;
        }
        @Override public String bookTwice(String address, int grams) throws TimeoutException {
            book(address, grams);                       // self-invocation: this.book, not the proxy
            return book(address, grams);
        }
        @Override public String toString() { return "RealCourier"; }
    }

    /** A fake clock: every read moves time forward by 7 ms. */
    private static LongSupplier ticking() {
        long[] now = {0};
        return () -> now[0] += 7_000_000;
    }

    private final List<String> records = new ArrayList<>();
    private final TimingProxy.MetricsSink sink = (name, nanos, failed) -> records.add(name + " " + nanos / 1_000_000 + "ms" + (failed ? " FAILED" : ""));

    @Test
    @DisplayName("The proxy implements the interface and forwards arguments and results")
    void forwards() throws Exception {
        RealCourier real = new RealCourier();
        CourierBooking proxy = TimingProxy.wrap(CourierBooking.class, real, ticking(), sink);
        assertThat(Proxy.isProxyClass(proxy.getClass())).isTrue();
        assertThat(proxy.book("12 Mill Lane", 1_250)).isEqualTo("PP-1250");
        assertThat(real.calls).isEqualTo(1);
    }

    @Test
    @DisplayName("Each call is reported as Interface.method with the time between two clock reads")
    void reportsTiming() throws Exception {
        CourierBooking proxy = TimingProxy.wrap(CourierBooking.class, new RealCourier(), ticking(), sink);
        proxy.book("12 Mill Lane", 1_250);
        proxy.book("3 Harbour Road", 990);
        assertThat(records).containsExactly("CourierBooking.book 7ms", "CourierBooking.book 7ms");
    }

    @Test
    @DisplayName("A runtime exception from the target reaches the caller unwrapped, and is reported as failed")
    void runtimeExceptionUnwrapped() {
        CourierBooking proxy = TimingProxy.wrap(CourierBooking.class, new RealCourier(), ticking(), sink);
        assertThatThrownBy(() -> proxy.book("12 Mill Lane", -1))
                .isExactlyInstanceOf(IllegalArgumentException.class)
                .hasMessage("negative weight");
        assertThat(records).containsExactly("CourierBooking.book 7ms FAILED");
    }

    @Test
    @DisplayName("A checked exception the interface declares reaches the caller as itself")
    void checkedExceptionUnwrapped() {
        CourierBooking proxy = TimingProxy.wrap(CourierBooking.class, new RealCourier(), ticking(), sink);
        assertThatThrownBy(() -> proxy.book("Gull Island pier", 100))
                .isExactlyInstanceOf(TimeoutException.class);
        assertThat(records).containsExactly("CourierBooking.book 7ms FAILED");
    }

    @Test
    @DisplayName("toString, equals and hashCode are forwarded but not timed")
    void objectMethodsNotTimed() {
        CourierBooking proxy = TimingProxy.wrap(CourierBooking.class, new RealCourier(), ticking(), sink);
        assertThat(proxy.toString()).isEqualTo("RealCourier");
        proxy.hashCode();
        assertThat(records).isEmpty();
    }

    @Test
    @DisplayName("Self-invocation skips the proxy: bookTwice is timed, its inner calls are not")
    void selfInvocationBypassesProxy() throws Exception {
        RealCourier real = new RealCourier();
        CourierBooking proxy = TimingProxy.wrap(CourierBooking.class, real, ticking(), sink);
        proxy.bookTwice("12 Mill Lane", 100);
        assertThat(real.calls).isEqualTo(2);
        assertThat(records).containsExactly("CourierBooking.bookTwice 7ms");
    }
}
