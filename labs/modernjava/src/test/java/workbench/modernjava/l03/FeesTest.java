package workbench.modernjava.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.modernjava.l03.Fees.BankTransfer;
import workbench.modernjava.l03.Fees.Card;
import workbench.modernjava.l03.Fees.Charge;
import workbench.modernjava.l03.Fees.Method;
import workbench.modernjava.l03.Fees.Money;
import workbench.modernjava.l03.Fees.Network;
import workbench.modernjava.l03.Fees.Region;
import workbench.modernjava.l03.Fees.Wallet;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class FeesTest {

    private static Charge charge(long minor, Method method, Region region) {
        return new Charge(new Money(minor, "EUR"), method, region);
    }

    private static Card consumer(Network n) { return new Card(n, false); }

    private static Card corporate(Network n) { return new Card(n, true); }

    @Test
    @DisplayName("card fees: AMEX 3.5%, corporate 2.9%, consumer 0.3% in the EEA and UK, 1.5% elsewhere")
    void cardFees() {
        assertThat(Fees.fee(charge(10_000, consumer(Network.AMEX), Region.EEA))).isEqualTo(350);
        assertThat(Fees.fee(charge(10_000, corporate(Network.VISA), Region.EEA))).isEqualTo(290);
        assertThat(Fees.fee(charge(10_000, consumer(Network.VISA), Region.EEA))).isEqualTo(30);
        assertThat(Fees.fee(charge(10_000, consumer(Network.MASTERCARD), Region.UK))).isEqualTo(30);
        assertThat(Fees.fee(charge(10_000, consumer(Network.VISA), Region.US))).isEqualTo(150);
        assertThat(Fees.fee(charge(10_000, consumer(Network.MASTERCARD), Region.OTHER))).isEqualTo(150);
    }

    @Test
    @DisplayName("rule order matters: a corporate AMEX pays the AMEX rate, a corporate VISA pays 2.9% in any region")
    void ruleOrder() {
        assertThat(Fees.fee(charge(10_000, corporate(Network.AMEX), Region.EEA))).isEqualTo(350);
        assertThat(Fees.fee(charge(10_000, corporate(Network.VISA), Region.US))).isEqualTo(290);
    }

    @Test
    @DisplayName("bank transfers are flat: 50 instant, 20 otherwise, whatever the amount")
    void transferFees() {
        assertThat(Fees.fee(charge(10_000, new BankTransfer(true), Region.US))).isEqualTo(50);
        assertThat(Fees.fee(charge(10_000, new BankTransfer(false), Region.US))).isEqualTo(20);
        assertThat(Fees.fee(charge(5_000_000, new BankTransfer(false), Region.EEA))).isEqualTo(20);
    }

    @Test
    @DisplayName("wallets are free under 1,000 minor units, then 1%")
    void walletFees() {
        assertThat(Fees.fee(charge(999, new Wallet("Paywave"), Region.EEA))).isEqualTo(0);
        assertThat(Fees.fee(charge(1_000, new Wallet("Paywave"), Region.EEA))).isEqualTo(10);
        assertThat(Fees.fee(charge(25_000, new Wallet("Paywave"), Region.US))).isEqualTo(250);
    }

    @Test
    @DisplayName("percentage fees round down")
    void roundsDown() {
        assertThat(Fees.fee(charge(33, consumer(Network.VISA), Region.EEA))).isEqualTo(0);
        assertThat(Fees.fee(charge(9_999, consumer(Network.VISA), Region.US))).isEqualTo(149);
    }

    @Test
    @DisplayName("fee(null) throws NullPointerException")
    void feeOfNull() {
        assertThatThrownBy(() -> Fees.fee(null)).isInstanceOf(NullPointerException.class);
    }

    @Test
    @DisplayName("label names each method, with AMEX first and corporate cards marked")
    void labels() {
        assertThat(Fees.label(corporate(Network.AMEX))).isEqualTo("AMEX");
        assertThat(Fees.label(consumer(Network.AMEX))).isEqualTo("AMEX");
        assertThat(Fees.label(corporate(Network.VISA))).isEqualTo("VISA corporate");
        assertThat(Fees.label(consumer(Network.MASTERCARD))).isEqualTo("MASTERCARD");
        assertThat(Fees.label(new BankTransfer(true))).isEqualTo("instant transfer");
        assertThat(Fees.label(new BankTransfer(false))).isEqualTo("transfer");
        assertThat(Fees.label(new Wallet("Paywave"))).isEqualTo("wallet Paywave");
    }

    @Test
    @DisplayName("label handles a null method and a wallet whose provider is null")
    void labelNulls() {
        assertThat(Fees.label(null)).isEqualTo("no method");
        assertThat(Fees.label(new Wallet(null))).isEqualTo("wallet ?");
    }
}
