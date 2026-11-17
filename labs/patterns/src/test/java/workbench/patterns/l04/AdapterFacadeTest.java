package workbench.patterns.l04;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.patterns.l04.OrderDesk.OrderResult;
import workbench.patterns.l04.Warehouse.StockResult;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;

class AdapterFacadeTest {

    /** A fake warehouse program: records what it was sent and answers with a canned string or exception. */
    static final class FakeWarehouse extends OldWarehouseSystem {
        final List<String> calls = new ArrayList<>();
        String answer = "00|H4711";
        WarehouseException failure;

        @Override
        public String hold(String itemNumber, String kilos) throws WarehouseException {
            calls.add(itemNumber + " " + kilos);
            if (failure != null) throw failure;
            return answer;
        }
    }

    @Test
    @DisplayName("The adapter sends item numbers and kilograms to the old program")
    void translatesArguments() {
        FakeWarehouse old = new FakeWarehouse();
        Warehouse warehouse = new WarehouseAdapter(old);
        warehouse.reserve("FLOUR", 1_250);
        warehouse.reserve("FLOUR", 5);
        warehouse.reserve("TEA", 250);
        assertThat(old.calls).containsExactly(
                "4711 1.250",
                "4711 0.005",
                "5150 0.250");
    }

    @Test
    @DisplayName("Answer 00 becomes Reserved with the hold id")
    void reserved() {
        FakeWarehouse old = new FakeWarehouse();
        old.answer = "00|H7Q2Z9";
        assertThat(new WarehouseAdapter(old).reserve("SUGAR", 1_000))
                .isEqualTo(new StockResult.Reserved("H7Q2Z9"));
    }

    @Test
    @DisplayName("Refusal codes become Refused with a reason in our words")
    void refusals() {
        FakeWarehouse old = new FakeWarehouse();
        Warehouse warehouse = new WarehouseAdapter(old);
        old.answer = "51|";
        assertThat(warehouse.reserve("SUGAR", 1_000)).isEqualTo(new StockResult.Refused("out of stock"));
        old.answer = "05|";
        assertThat(warehouse.reserve("SUGAR", 1_000)).isEqualTo(new StockResult.Refused("discontinued"));
        old.answer = "14|";
        assertThat(warehouse.reserve("SUGAR", 1_000)).isEqualTo(new StockResult.Refused("warehouse code 14"));
    }

    @Test
    @DisplayName("A WarehouseException becomes Unavailable and never escapes the adapter")
    void vendorExceptionIsTranslated() {
        FakeWarehouse old = new FakeWarehouse();
        old.failure = new WarehouseException(503, "warehouse line busy after 120 ms");
        Warehouse warehouse = new WarehouseAdapter(old);
        assertThatCode(() -> warehouse.reserve("SUGAR", 1_000)).doesNotThrowAnyException();
        assertThat(warehouse.reserve("SUGAR", 1_000))
                .isEqualTo(new StockResult.Unavailable("warehouse line busy after 120 ms"));
    }

    @Test
    @DisplayName("The adapter works against the real pretend warehouse too")
    void realPretendWarehouse() {
        Warehouse warehouse = new WarehouseAdapter(new OldWarehouseSystem());
        assertThat(warehouse.reserve("FLOUR", 50_000)).isEqualTo(new StockResult.Reserved("H4711"));
        assertThat(warehouse.reserve("FLOUR", 50_001)).isEqualTo(new StockResult.Refused("out of stock"));
    }

    // ---- facade ----

    private final List<String> recorded = new ArrayList<>();
    private final List<String> sent = new ArrayList<>();
    private final OrderDesk.OrderBook orderBook = (order, product, grams, hold) -> recorded.add(order + " " + product + " " + grams + " " + hold);
    private final OrderDesk.Notifier notifier = (email, message) -> sent.add(email + ": " + message);

    @Test
    @DisplayName("Reserved: write it in the order book, send a confirmation, return Placed")
    void deskReserved() {
        OrderDesk desk = new OrderDesk((product, grams) -> new StockResult.Reserved("H4711"), orderBook, notifier);
        assertThat(desk.place("o-1", "FLOUR", 1_250, "anna@example.com"))
                .isEqualTo(new OrderResult.Placed("H4711"));
        assertThat(recorded).containsExactly("o-1 FLOUR 1250 H4711");
        assertThat(sent).containsExactly("anna@example.com: Order o-1: 1.250 kg of FLOUR is on its way");
    }

    @Test
    @DisplayName("Refused: nothing written, a sorry note, return Refused")
    void deskRefused() {
        OrderDesk desk = new OrderDesk((product, grams) -> new StockResult.Refused("out of stock"), orderBook, notifier);
        assertThat(desk.place("o-2", "FLOUR", 1_250, "anna@example.com"))
                .isEqualTo(new OrderResult.Refused("out of stock"));
        assertThat(recorded).isEmpty();
        assertThat(sent).containsExactly("anna@example.com: Sorry, order o-2 failed: out of stock");
    }

    @Test
    @DisplayName("Unavailable: nothing written, nothing sent, return RetryLater")
    void deskUnavailable() {
        OrderDesk desk = new OrderDesk((product, grams) -> new StockResult.Unavailable("line busy"), orderBook, notifier);
        assertThat(desk.place("o-3", "FLOUR", 1_250, "anna@example.com"))
                .isEqualTo(new OrderResult.RetryLater());
        assertThat(recorded).isEmpty();
        assertThat(sent).isEmpty();
    }

    @Test
    @DisplayName("A failing notifier does not fail an order that was reserved and written down")
    void notifierFailureIsContained() {
        OrderDesk.Notifier broken = (email, message) -> { throw new IllegalStateException("mail server down"); };
        OrderDesk desk = new OrderDesk((product, grams) -> new StockResult.Reserved("H4711"), orderBook, broken);
        assertThat(desk.place("o-4", "FLOUR", 990, "anna@example.com"))
                .isEqualTo(new OrderResult.Placed("H4711"));
        assertThat(recorded).containsExactly("o-4 FLOUR 990 H4711");
    }

    @Test
    @DisplayName("Desk plus adapter: a tea order goes through the old program and into the order book")
    void endToEnd() {
        FakeWarehouse old = new FakeWarehouse();
        old.answer = "00|T0001";
        OrderDesk desk = new OrderDesk(new WarehouseAdapter(old), orderBook, notifier);
        assertThat(desk.place("o-5", "TEA", 250, "kenji@example.com"))
                .isEqualTo(new OrderResult.Placed("T0001"));
        assertThat(old.calls).containsExactly("5150 0.250");
        assertThat(sent).containsExactly("kenji@example.com: Order o-5: 0.250 kg of TEA is on its way");
    }
}
