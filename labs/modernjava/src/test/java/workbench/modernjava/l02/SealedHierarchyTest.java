package workbench.modernjava.l02;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.modernjava.l02.PaymentMethod.BankTransfer;
import workbench.modernjava.l02.PaymentMethod.Card;
import workbench.modernjava.l02.PaymentMethod.PartnerMethod;
import workbench.modernjava.l02.PaymentMethod.Sepa;
import workbench.modernjava.l02.PaymentMethod.Swift;
import workbench.modernjava.l02.PaymentMethod.Wallet;

import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.SimpleJavaFileObject;
import javax.tools.ToolProvider;
import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.util.List;
import java.util.Locale;

import static org.assertj.core.api.Assertions.assertThat;

class SealedHierarchyTest {

    // a partner team's own class, written outside the hierarchy's file
    record GiftCard(String partnerId, int settlementDays) implements PartnerMethod {}

    @Test
    @DisplayName("PaymentMethod is sealed and permits exactly Card, BankTransfer, Wallet and PartnerMethod")
    void paymentMethodIsSealed() {
        assertThat(PaymentMethod.class.isSealed()).isTrue();
        assertThat(PaymentMethod.class.getPermittedSubclasses())
                .containsExactlyInAnyOrder(Card.class, BankTransfer.class, Wallet.class, PartnerMethod.class);
    }

    @Test
    @DisplayName("BankTransfer is sealed too, with only Sepa and Swift")
    void bankTransferIsSealed() {
        assertThat(BankTransfer.class.isSealed()).isTrue();
        assertThat(BankTransfer.class.getPermittedSubclasses()).containsExactlyInAnyOrder(Sepa.class, Swift.class);
    }

    @Test
    @DisplayName("PartnerMethod stays open, and a partner's own class settles on its own schedule")
    void partnerMethodIsOpen() {
        assertThat(PartnerMethod.class.isSealed()).isFalse();
        assertThat(Settlement.daysToSettle(new GiftCard("giftly", 5))).isEqualTo(5);
        assertThat(Settlement.rail(new GiftCard("giftly", 5))).isEqualTo("partner:giftly");
    }

    @Test
    @DisplayName("daysToSettle: card 2, SEPA 1, SWIFT 3, wallet 0")
    void daysToSettle() {
        assertThat(Settlement.daysToSettle(new Card("VISA", "1111"))).isEqualTo(2);
        assertThat(Settlement.daysToSettle(new Sepa("DE89370400440532013000"))).isEqualTo(1);
        assertThat(Settlement.daysToSettle(new Swift("DEUTDEFF", "0532013000"))).isEqualTo(3);
        assertThat(Settlement.daysToSettle(new Wallet("Paywave"))).isEqualTo(0);
    }

    @Test
    @DisplayName("rail names the rail, with one answer for every kind of bank transfer")
    void rail() {
        assertThat(Settlement.rail(new Card("VISA", "1111"))).isEqualTo("card");
        assertThat(Settlement.rail(new Sepa("DE89370400440532013000"))).isEqualTo("bank");
        assertThat(Settlement.rail(new Swift("DEUTDEFF", "0532013000"))).isEqualTo("bank");
        assertThat(Settlement.rail(new Wallet("Paywave"))).isEqualTo("wallet");
    }

    @Test
    @DisplayName("javac accepts a switch with one case per permitted type and no default")
    void exhaustiveSwitchCompiles() throws IOException {
        List<String> errors = compile("Client", """
                package client;
                import workbench.modernjava.l02.PaymentMethod;
                import workbench.modernjava.l02.PaymentMethod.*;
                class Client {
                    static String f(PaymentMethod m) {
                        return switch (m) {
                            case Card c -> "card";
                            case Sepa s -> "sepa";
                            case Swift s -> "swift";
                            case Wallet w -> "wallet";
                            case PartnerMethod p -> "partner";
                        };
                    }
                }
                """);
        assertThat(errors).as("javac errors").isEmpty();
    }

    @Test
    @DisplayName("javac rejects a new payment method or a new bank transfer written outside the hierarchy")
    void outsidersAreRejected() throws IOException {
        List<String> crypto = compile("Crypto", """
                package client;
                final class Crypto implements workbench.modernjava.l02.PaymentMethod {}
                """);
        assertThat(crypto).as("javac errors for Crypto").singleElement()
                .asString().contains("not allowed to extend sealed class");

        List<String> ach = compile("Ach", """
                package client;
                final class Ach implements workbench.modernjava.l02.PaymentMethod.BankTransfer {}
                """);
        assertThat(ach).as("javac errors for Ach").singleElement()
                .asString().contains("not allowed to extend sealed class");
    }

    /** Compiles one source file against the classes under test and returns javac's error messages. */
    static List<String> compile(String className, String source) throws IOException {
        JavaCompiler javac = ToolProvider.getSystemJavaCompiler();
        assertThat(javac).as("run the tests on a JDK, not a JRE").isNotNull();
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        JavaFileObject file = new SimpleJavaFileObject(
                URI.create("string:///client/" + className + ".java"), JavaFileObject.Kind.SOURCE) {
            @Override
            public CharSequence getCharContent(boolean ignoreEncodingErrors) { return source; }
        };
        String out = Files.createTempDirectory("l02-javac").toString();
        List<String> options = List.of("--release", "21", "-d", out,
                "-classpath", System.getProperty("java.class.path"));
        javac.getTask(null, null, diagnostics, options, null, List.of(file)).call();
        return diagnostics.getDiagnostics().stream()
                .filter(d -> d.getKind() == Diagnostic.Kind.ERROR)
                .map(d -> d.getMessage(Locale.ROOT))
                .toList();
    }
}
