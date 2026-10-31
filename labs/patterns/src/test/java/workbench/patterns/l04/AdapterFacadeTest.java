package workbench.patterns.l04;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.patterns.l04.CardAuthorizer.AuthResult;
import workbench.patterns.l04.CheckoutFacade.CheckoutResult;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;

class AdapterFacadeTest {

    /** A fake vendor SDK: records what it was sent and answers with a canned response or exception. */
    static final class FakeSdk extends LegacyIssuerSdk {
        final List<String> calls = new ArrayList<>();
        String response = "00|A1111";
        SdkException failure;

        @Override
        public String auth(String pan, String amount, String currencyNumeric) throws SdkException {
            calls.add(pan + " " + amount + " " + currencyNumeric);
            if (failure != null) throw failure;
            return response;
        }
    }

    @Test
    @DisplayName("The adapter sends decimal amounts and numeric currency codes to the SDK")
    void translatesArguments() {
        FakeSdk sdk = new FakeSdk();
        CardAuthorizer auth = new IssuerSdkAdapter(sdk);
        auth.authorize("4111111111111111", 1_250, "EUR");
        auth.authorize("4111111111111111", 5, "EUR");
        auth.authorize("4111111111111111", 1_250, "JPY");
        assertThat(sdk.calls).containsExactly(
                "4111111111111111 12.50 978",
                "4111111111111111 0.05 978",
                "4111111111111111 1250 392");
    }

    @Test
    @DisplayName("Response 00 becomes Approved with the auth id")
    void approved() {
        FakeSdk sdk = new FakeSdk();
        sdk.response = "00|A7Q2Z9";
        assertThat(new IssuerSdkAdapter(sdk).authorize("4111111111111111", 100, "EUR"))
                .isEqualTo(new AuthResult.Approved("A7Q2Z9"));
    }

    @Test
    @DisplayName("Decline codes become Declined with a reason in our words")
    void declines() {
        FakeSdk sdk = new FakeSdk();
        CardAuthorizer auth = new IssuerSdkAdapter(sdk);
        sdk.response = "51|";
        assertThat(auth.authorize("4111111111111111", 100, "EUR")).isEqualTo(new AuthResult.Declined("insufficient funds"));
        sdk.response = "05|";
        assertThat(auth.authorize("4111111111111111", 100, "EUR")).isEqualTo(new AuthResult.Declined("do not honor"));
        sdk.response = "14|";
        assertThat(auth.authorize("4111111111111111", 100, "EUR")).isEqualTo(new AuthResult.Declined("issuer code 14"));
    }

    @Test
    @DisplayName("An SdkException becomes Unavailable and never escapes the adapter")
    void vendorExceptionIsTranslated() {
        FakeSdk sdk = new FakeSdk();
        sdk.failure = new SdkException(503, "issuer timeout after 120 ms");
        CardAuthorizer auth = new IssuerSdkAdapter(sdk);
        assertThatCode(() -> auth.authorize("4111111111111111", 100, "EUR")).doesNotThrowAnyException();
        assertThat(auth.authorize("4111111111111111", 100, "EUR"))
                .isEqualTo(new AuthResult.Unavailable("issuer timeout after 120 ms"));
    }

    @Test
    @DisplayName("The adapter works against the real sandbox SDK too")
    void realSandbox() {
        CardAuthorizer auth = new IssuerSdkAdapter(new LegacyIssuerSdk());
        assertThat(auth.authorize("4111111111111111", 99_999, "EUR")).isEqualTo(new AuthResult.Approved("A1111"));
        assertThat(auth.authorize("4111111111111111", 100_000, "EUR")).isEqualTo(new AuthResult.Declined("insufficient funds"));
    }

    // ---- facade ----

    private final List<String> posted = new ArrayList<>();
    private final List<String> sent = new ArrayList<>();
    private final CheckoutFacade.Ledger ledger = (order, amount, currency, code) -> posted.add(order + " " + amount + " " + currency + " " + code);
    private final CheckoutFacade.Notifier notifier = (email, message) -> sent.add(email + ": " + message);

    @Test
    @DisplayName("Approved: post to the ledger, send a receipt, return Paid")
    void facadeApproved() {
        CheckoutFacade facade = new CheckoutFacade((pan, amount, cur) -> new AuthResult.Approved("A1111"), ledger, notifier);
        assertThat(facade.checkout("o-1", "4111111111111111", 1_250, "EUR", "anna@example.com"))
                .isEqualTo(new CheckoutResult.Paid("A1111"));
        assertThat(posted).containsExactly("o-1 1250 EUR A1111");
        assertThat(sent).containsExactly("anna@example.com: Paid 12.50 EUR for order o-1");
    }

    @Test
    @DisplayName("Declined: no ledger post, a decline notice, return Declined")
    void facadeDeclined() {
        CheckoutFacade facade = new CheckoutFacade((pan, amount, cur) -> new AuthResult.Declined("insufficient funds"), ledger, notifier);
        assertThat(facade.checkout("o-2", "4111111111111111", 1_250, "EUR", "anna@example.com"))
                .isEqualTo(new CheckoutResult.Declined("insufficient funds"));
        assertThat(posted).isEmpty();
        assertThat(sent).containsExactly("anna@example.com: Payment declined: insufficient funds");
    }

    @Test
    @DisplayName("Unavailable: nothing posted, nothing sent, return RetryLater")
    void facadeUnavailable() {
        CheckoutFacade facade = new CheckoutFacade((pan, amount, cur) -> new AuthResult.Unavailable("timeout"), ledger, notifier);
        assertThat(facade.checkout("o-3", "4111111111111111", 1_250, "EUR", "anna@example.com"))
                .isEqualTo(new CheckoutResult.RetryLater());
        assertThat(posted).isEmpty();
        assertThat(sent).isEmpty();
    }

    @Test
    @DisplayName("A failing notifier does not fail a payment that was approved and posted")
    void notifierFailureIsContained() {
        CheckoutFacade.Notifier broken = (email, message) -> { throw new IllegalStateException("SMTP down"); };
        CheckoutFacade facade = new CheckoutFacade((pan, amount, cur) -> new AuthResult.Approved("A1111"), ledger, broken);
        assertThat(facade.checkout("o-4", "4111111111111111", 990, "EUR", "anna@example.com"))
                .isEqualTo(new CheckoutResult.Paid("A1111"));
        assertThat(posted).containsExactly("o-4 990 EUR A1111");
    }

    @Test
    @DisplayName("Facade plus adapter: a JPY payment goes through the SDK and onto the ledger")
    void endToEnd() {
        FakeSdk sdk = new FakeSdk();
        sdk.response = "00|J0001";
        CheckoutFacade facade = new CheckoutFacade(new IssuerSdkAdapter(sdk), ledger, notifier);
        assertThat(facade.checkout("o-5", "4111111111111111", 1_250, "JPY", "kenji@example.com"))
                .isEqualTo(new CheckoutResult.Paid("J0001"));
        assertThat(sdk.calls).containsExactly("4111111111111111 1250 392");
        assertThat(sent).containsExactly("kenji@example.com: Paid 1250 JPY for order o-5");
    }
}
