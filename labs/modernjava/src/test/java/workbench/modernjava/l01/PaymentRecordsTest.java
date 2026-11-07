package workbench.modernjava.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class PaymentRecordsTest {

    private static Money eur(long minor) { return new Money(minor, "EUR"); }

    // ---- Money ----

    @Test
    @DisplayName("Money trims and upper-cases the currency, so \" eur \" and \"EUR\" are the same value")
    void moneyNormalizesCurrency() {
        Money m = new Money(1_250, " eur ");
        assertThat(m.currency()).isEqualTo("EUR");
        assertThat(m).isEqualTo(eur(1_250));
        assertThat(m.hashCode()).isEqualTo(eur(1_250).hashCode());
    }

    @Test
    @DisplayName("Money rejects a negative amount, a currency that is not three letters, and a null currency")
    void moneyRejectsBadInput() {
        assertThatThrownBy(() -> new Money(-1, "EUR")).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new Money(100, "EURO")).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new Money(100, "E1R")).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new Money(100, null))
                .isInstanceOf(NullPointerException.class)
                .hasMessageContaining("currency");
    }

    @Test
    @DisplayName("Money.plus adds amounts in one currency and refuses to mix currencies or overflow")
    void moneyPlus() {
        assertThat(eur(1_250).plus(new Money(250, "eur"))).isEqualTo(eur(1_500));
        assertThatThrownBy(() -> eur(1).plus(new Money(1, "USD"))).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> eur(Long.MAX_VALUE).plus(eur(1))).isInstanceOf(ArithmeticException.class);
    }

    // ---- Refund ----

    @Test
    @DisplayName("Refund keeps its own copy of the reasons: the caller's later changes don't leak in")
    void refundCopiesReasons() {
        List<String> reasons = new ArrayList<>(List.of("duplicate charge"));
        Refund r = new Refund("pay_81", eur(500), reasons);
        Set<Refund> seen = new HashSet<>(Set.of(r));

        reasons.add("customer asked twice");

        assertThat(r.reasons()).containsExactly("duplicate charge");
        assertThat(seen).as("a refund used as a set key must stay findable").contains(r);
        assertThatThrownBy(() -> r.reasons().add("x")).isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    @DisplayName("Refund rejects a blank payment id, no reasons, and null parts")
    void refundRejectsBadInput() {
        assertThatThrownBy(() -> new Refund("  ", eur(500), List.of("dup"))).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new Refund("pay_81", eur(500), List.of())).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new Refund("pay_81", null, List.of("dup"))).isInstanceOf(NullPointerException.class);
        assertThatThrownBy(() -> new Refund(null, eur(500), List.of("dup"))).isInstanceOf(NullPointerException.class);
    }

    @Test
    @DisplayName("withAmount returns a new refund, leaves the old one alone, and validates the new amount")
    void refundWither() {
        Refund full = new Refund("pay_81", eur(500), List.of("dup"));
        Refund part = full.withAmount(eur(200));

        assertThat(part).isEqualTo(new Refund("pay_81", eur(200), List.of("dup")));
        assertThat(full.amount()).isEqualTo(eur(500));
        assertThatThrownBy(() -> full.withAmount(null)).isInstanceOf(NullPointerException.class);
    }

    // ---- CardNumber ----

    @Test
    @DisplayName("CardNumber strips spaces and accepts only 12 to 19 digits")
    void cardNumberValidates() {
        assertThat(new CardNumber("4111 1111 1111 1111").digits()).isEqualTo("4111111111111111");
        assertThatThrownBy(() -> new CardNumber("1234")).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new CardNumber("4111-1111-1111-1111")).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new CardNumber(null)).isInstanceOf(NullPointerException.class);
    }

    @Test
    @DisplayName("CardNumber.toString shows only the last four digits, and equality still uses the real number")
    void cardNumberMasksToString() {
        CardNumber c = new CardNumber("4111111111111111");
        assertThat(c.toString()).isEqualTo("CardNumber[****1111]");
        assertThat(c.last4()).isEqualTo("1111");
        assertThat(c.digits()).as("the accessor is not masked").isEqualTo("4111111111111111");
        // the record contract: a copy built from the accessors equals the original
        assertThat(new CardNumber(c.digits())).isEqualTo(c);
        assertThat(new CardNumber("5500000000000004")).isNotEqualTo(c);
    }
}
