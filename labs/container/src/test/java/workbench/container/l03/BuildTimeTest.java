package workbench.container.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import workbench.container.l03.app.CardIssuerClient;
import workbench.container.l03.app.FeeCalculator;
import workbench.container.l03.app.FxRates;
import workbench.container.l03.app.HttpIssuerClient;
import workbench.container.l03.app.IssuerConfig;
import workbench.container.l03.app.IssuerScript;
import workbench.container.l03.app.Ledger;
import workbench.container.l03.app.PaymentAttempt;
import workbench.container.l03.app.PaymentService;
import workbench.container.l03.app.RateQuoter;
import workbench.container.l03.app.SlowRates;

import java.lang.reflect.Proxy;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CountDownLatch;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class BuildTimeTest {
    private static final String NAME = "workbench.container.l03.gen.AppRegistry";
    private static final List<Class<?>> APP = List.of(PaymentService.class, PaymentAttempt.class, Ledger.class,
            FeeCalculator.class, FxRates.class, HttpIssuerClient.class, IssuerConfig.class, IssuerScript.class,
            SettlementService.class, SettlementLedger.class, RateQuoter.class, SlowRates.class);

    @TempDir
    static Path build;
    private static String source;
    private static Path classes;

    // the "build": generate and compile once, on first use; every test then loads a fresh copy of the class
    private static synchronized String source() {
        if (source == null) {
            String generated = RegistryGenerator.generate("workbench.container.l03.gen", "AppRegistry", APP);
            classes = GeneratedCode.compile(NAME, generated, build);
            source = generated;
        }
        return source;
    }

    private static Registry generated() {
        source();
        return GeneratedCode.load(classes, NAME);
    }

    public static class Payouts { public Payouts(Statements s) {} }
    public static class Statements { public Statements(Payouts p) {} }

    /** The checks that make two registries "the same graph". */
    private static void assertWiring(Registry r) {
        PaymentService payments = r.get(PaymentService.class);
        assertThat(r.get(PaymentService.class)).isSameAs(payments);
        assertThat(payments.fees()).isSameAs(r.get(FeeCalculator.class));
        assertThat(payments.fees().rates()).isSameAs(r.get(FxRates.class));
        assertThat(payments.ledger()).isSameAs(r.get(Ledger.class));
        assertThat(payments.issuer()).isSameAs(r.get(CardIssuerClient.class));
        assertThat(r.get(PaymentAttempt.class).fees()).isSameAs(payments.fees());
        assertThat(r.get(RateQuoter.class).rates()).isSameAs(r.get(SlowRates.class));
    }

    @Test
    @DisplayName("the generated registry wires the same graph as the reflective container, in the same order")
    void sameGraph() {
        Registry reflective = new Container(APP);
        Registry generated = generated();
        assertWiring(reflective);
        assertWiring(generated);
        assertThat(generated.creationOrder()).isEqualTo(reflective.creationOrder());

        for (Registry r : List.of(reflective, generated)) {           // and it behaves the same
            r.get(IssuerScript.class).failures.set(2);
            assertThat(r.get(PaymentService.class).pay("4111111111111111", 12_000)).isEqualTo("auth-1111-12000");
            assertThat(r.get(IssuerScript.class).calls.get()).as("issuer calls, retries included").isEqualTo(3);
            assertThat(r.get(Ledger.class).lines()).containsExactly("auth-1111-12000 fee=320");
            assertThat(r.callLog().names()).containsExactly("CardIssuerClient.authorize");
        }
    }

    @Test
    @DisplayName("generated singletons are built on first get, once, after their dependencies")
    void holdersAreLazy() {
        Registry r = generated();
        int rates = SlowRates.CREATED.get();
        int quoters = RateQuoter.CREATED.get();
        r.get(SlowRates.class);
        assertThat(SlowRates.CREATED.get() - rates).isEqualTo(1);
        assertThat(RateQuoter.CREATED.get() - quoters).as("RateQuoter, which nobody asked for").isZero();
        r.get(RateQuoter.class);
        r.get(RateQuoter.class);
        assertThat(RateQuoter.CREATED.get() - quoters).isEqualTo(1);
        assertThat(SlowRates.CREATED.get() - rates).isEqualTo(1);
    }

    @Test
    @DisplayName("eight threads asking a fresh generated registry at once get one instance, built once")
    void oneInstanceUnderConcurrentFirstAccess() throws Exception {
        Registry r = generated();
        int rates = SlowRates.CREATED.get();
        int quoters = RateQuoter.CREATED.get();
        CountDownLatch go = new CountDownLatch(1);
        Set<Object> seen = Collections.synchronizedSet(Collections.newSetFromMap(new IdentityHashMap<>()));
        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            Thread t = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                seen.add(r.get(RateQuoter.class));
            });
            t.start();
            threads.add(t);
        }
        go.countDown();
        for (Thread t : threads) t.join();
        assertThat(seen).hasSize(1);
        assertThat(SlowRates.CREATED.get() - rates).isEqualTo(1);
        assertThat(RateQuoter.CREATED.get() - quoters).isEqualTo(1);
    }

    @Test
    @DisplayName("a generated prototype is new on every get")
    void prototypes() {
        Registry r = generated();
        assertThat(r.get(PaymentAttempt.class)).isNotSameAs(r.get(PaymentAttempt.class));
    }

    @Test
    @DisplayName("interception is generated code too: a forwarding class and a subclass, no JDK proxy, no Byte Buddy")
    void generatedProxies() {
        Registry r = generated();
        CardIssuerClient issuer = r.get(CardIssuerClient.class);
        assertThat(Proxy.isProxyClass(issuer.getClass())).isFalse();
        assertThat(issuer.getClass().getName()).isEqualTo(NAME + "$HttpIssuerClient_Proxy");
        assertThat(issuer.equals(issuer)).isTrue();
        assertThat(issuer.authorizeSmall("4111111111111111")).isEqualTo("auth-1111-5000");

        SettlementService settlement = r.get(SettlementService.class);
        assertThat(settlement.getClass().getName()).isEqualTo(NAME + "$SettlementService_Intercepted");
        assertThat(settlement.settle("B-17")).isEqualTo("settled B-17");
        assertThat(r.callLog().names()).containsExactly(
                "CardIssuerClient.authorize", "SettlementService.audit", "SettlementService.settle");
    }

    @Test
    @DisplayName("the generated source calls constructors directly: no reflection, no class lookups by name")
    void plainCode() {
        assertThat(source())
                .contains("new workbench.container.l03.app.FeeCalculator(FxRates_Holder.INSTANCE)")
                .doesNotContain("java.lang.reflect", "getConstructor", "newInstance", "Class.forName",
                        "ByteBuddy", "Proxy.newProxyInstance", "getAnnotation");
    }

    @Test
    @DisplayName("a cycle fails the build, with the same message the container gives at start-up")
    void cycleFailsTheBuild() {
        assertThatThrownBy(() -> RegistryGenerator.generate("x", "Broken", List.of(Payouts.class, Statements.class)))
                .isInstanceOf(ContainerException.class)
                .hasMessage("Dependency cycle: Payouts -> Statements -> Payouts");
    }
}
