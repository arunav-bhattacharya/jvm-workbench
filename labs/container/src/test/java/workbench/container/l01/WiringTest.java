package workbench.container.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.container.l01.app.CardIssuerClient;
import workbench.container.l01.app.FeeCalculator;
import workbench.container.l01.app.FxRates;
import workbench.container.l01.app.HttpIssuerClient;
import workbench.container.l01.app.InitLog;
import workbench.container.l01.app.IssuerConfig;
import workbench.container.l01.app.Ledger;
import workbench.container.l01.app.NotAComponent;
import workbench.container.l01.app.PaymentAttempt;
import workbench.container.l01.app.PaymentService;
import workbench.container.l01.app.ScanProbe;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class WiringTest {
    private static final List<Class<?>> APP = List.of(PaymentService.class, PaymentAttempt.class, Ledger.class,
            FeeCalculator.class, FxRates.class, HttpIssuerClient.class, IssuerConfig.class);

    // --- fixtures with cycles and slow constructors, listed explicitly instead of scanned -----------

    public static class Payouts { public Payouts(Statements s) {} }
    public static class Statements { public Statements(Reconciler r) {} }
    public static class Reconciler { public Reconciler(Payouts p) {} }
    public static class Dashboard { public Dashboard(Payouts p) {} }
    public static class Selfish { public Selfish(Selfish s) {} }

    public static class TwoDoors {
        public TwoDoors() {}
        public TwoDoors(FxRates rates) {}
    }

    public static class Marked {
        public Marked() {}
        @Inject public Marked(FxRates rates) {}
    }

    public static class SlowRates {
        static final AtomicInteger CREATED = new AtomicInteger();
        public SlowRates() throws InterruptedException {
            CREATED.incrementAndGet();
            Thread.sleep(50);                       // a slow start, so racing threads overlap inside it
        }
    }

    public static class RateQuoter {
        static final AtomicInteger CREATED = new AtomicInteger();
        final SlowRates rates;
        public RateQuoter(SlowRates rates) {
            CREATED.incrementAndGet();
            this.rates = rates;
        }
    }

    public static class Exploding {
        public Exploding() { throw new IllegalStateException("issuer key missing"); }
    }

    // --- constructors --------------------------------------------------------------------------

    @Test
    @DisplayName("pick returns the only public constructor")
    void picksTheOnlyConstructor() throws Exception {
        assertThat(Constructors.pick(FeeCalculator.class)).isEqualTo(FeeCalculator.class.getConstructor(FxRates.class));
    }

    @Test
    @DisplayName("pick prefers the @Inject constructor, and refuses to guess between two unmarked ones")
    void injectWinsAndTwoIsAmbiguous() throws Exception {
        assertThat(Constructors.pick(Marked.class)).isEqualTo(Marked.class.getConstructor(FxRates.class));
        assertThatThrownBy(() -> Constructors.pick(TwoDoors.class))
                .isInstanceOf(ContainerException.class)
                .hasMessage("TwoDoors has 2 public constructors; mark the one to use with @Inject");
    }

    @Test
    @DisplayName("pick ignores Kotlin's synthetic constructor for default arguments")
    void kotlinSyntheticConstructor() throws Exception {
        assertThat(KotlinFees.class.getConstructors()).hasSize(2);
        assertThat(Constructors.pick(KotlinFees.class)).isEqualTo(KotlinFees.class.getConstructor(FxRates.class, int.class));
    }

    @Test
    @DisplayName("a Kotlin class whose parameters all have defaults has two real constructors, even with @Inject")
    void kotlinAllDefaults() {
        assertThatThrownBy(() -> Constructors.pick(DefaultedFees.class))
                .isInstanceOf(ContainerException.class)
                .hasMessage("DefaultedFees has 2 public constructors; mark the one to use with @Inject");
        assertThatThrownBy(() -> Constructors.pick(InjectedFees.class))
                .isInstanceOf(ContainerException.class)
                .hasMessage("InjectedFees has 2 @Inject constructors; keep one");
    }

    // --- the graph -------------------------------------------------------------------------------

    @Test
    @DisplayName("creation order lists every component once, each after all of its dependencies")
    void dependenciesComeFirst() {
        BeanGraph graph = new BeanGraph(APP);
        List<Class<?>> order = graph.creationOrder();
        assertThat(order).containsExactlyInAnyOrderElementsOf(APP);
        for (Class<?> c : order) {
            for (Class<?> dep : graph.dependenciesOf(c)) {
                assertThat(order.indexOf(dep)).as(dep.getSimpleName() + " before " + c.getSimpleName())
                        .isLessThan(order.indexOf(c));
            }
        }
    }

    @Test
    @DisplayName("a cycle is reported with its path, from the repeated class back to itself")
    void cycleMessage() {
        assertThatThrownBy(() -> new BeanGraph(List.of(Payouts.class, Statements.class, Reconciler.class)).creationOrder())
                .isInstanceOf(ContainerException.class)
                .hasMessage("Dependency cycle: Payouts -> Statements -> Reconciler -> Payouts");
        assertThatThrownBy(() -> new BeanGraph(List.of(Dashboard.class, Payouts.class, Statements.class, Reconciler.class)).creationOrder())
                .as("the path starts at the cycle, not at Dashboard")
                .hasMessage("Dependency cycle: Payouts -> Statements -> Reconciler -> Payouts");
        assertThatThrownBy(() -> new BeanGraph(List.of(Selfish.class)).creationOrder())
                .hasMessage("Dependency cycle: Selfish -> Selfish");
    }

    @Test
    @DisplayName("the container checks the whole graph when it is built, before anyone asks for a bean")
    void failsFast() {
        assertThatThrownBy(() -> new Container(List.of(Dashboard.class, Payouts.class, Statements.class, Reconciler.class)))
                .isInstanceOf(ContainerException.class)
                .hasMessageContaining("Dependency cycle");
        assertThatThrownBy(() -> new Container(List.of(PaymentService.class, Ledger.class)))
                .isInstanceOf(ContainerException.class)
                .hasMessage("PaymentService needs CardIssuerClient: No component provides CardIssuerClient");
    }

    // --- scopes --------------------------------------------------------------------------------

    @Test
    @DisplayName("a singleton is created once and shared by everyone who needs it")
    void singletonsAreShared() {
        Container c = new Container(APP);
        PaymentService payments = c.get(PaymentService.class);
        assertThat(c.get(PaymentService.class)).isSameAs(payments);
        assertThat(payments.fees()).isSameAs(c.get(FeeCalculator.class));
        assertThat(payments.fees().rates()).isSameAs(c.get(FxRates.class));
        assertThat(payments.issuer()).isInstanceOf(HttpIssuerClient.class).isSameAs(c.get(CardIssuerClient.class));
        assertThat(((HttpIssuerClient) payments.issuer()).config()).isSameAs(c.get(IssuerConfig.class));
        assertThat(payments.pay("4111111111111111", 12_000)).isEqualTo("auth-1111-12000");
        assertThat(c.get(Ledger.class).lines()).containsExactly("auth-1111-12000 fee=348");
    }

    @Test
    @DisplayName("a prototype is new on every get, while its singleton dependencies are shared")
    void prototypesAreNew() {
        Container c = new Container(APP);
        PaymentAttempt first = c.get(PaymentAttempt.class);
        PaymentAttempt second = c.get(PaymentAttempt.class);
        assertThat(first).isNotSameAs(second);
        assertThat(first.fees()).isSameAs(second.fees()).isSameAs(c.get(FeeCalculator.class));
    }

    @Test
    @DisplayName("eight threads asking for a new singleton at once get one instance, built once")
    void oneInstanceUnderConcurrentFirstAccess() throws Exception {
        Container c = new Container(List.of(RateQuoter.class, SlowRates.class));
        int ratesBefore = SlowRates.CREATED.get();
        int quotersBefore = RateQuoter.CREATED.get();
        CountDownLatch go = new CountDownLatch(1);
        Set<Object> seen = ConcurrentHashMap.newKeySet();
        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            Thread t = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                seen.add(c.get(RateQuoter.class));
            });
            t.start();
            threads.add(t);
        }
        go.countDown();
        for (Thread t : threads) t.join();
        assertThat(seen).hasSize(1);
        assertThat(SlowRates.CREATED.get() - ratesBefore).as("SlowRates constructor calls").isEqualTo(1);
        assertThat(RateQuoter.CREATED.get() - quotersBefore).as("RateQuoter constructor calls").isEqualTo(1);
    }

    @Test
    @DisplayName("a failing constructor surfaces its own exception as the cause, and a later get tries again")
    void constructorFailure() {
        Container c = new Container(List.of(Exploding.class));
        for (int attempt = 0; attempt < 2; attempt++) {
            assertThatThrownBy(() -> c.get(Exploding.class))
                    .isInstanceOf(ContainerException.class)
                    .hasMessageContaining("Exploding")
                    .cause().isInstanceOf(IllegalStateException.class).hasMessage("issuer key missing");
        }
    }

    // --- scanning (given code: these pass from the start) ---------------------------------------

    @Test
    @DisplayName("the scanner finds the @Component classes of one package without initializing them")
    void scanFindsComponents() {
        List<Class<?>> found = ClassScanner.scan(getClass().getClassLoader(), "workbench.container.l01.app");
        assertThat(found).contains(PaymentService.class, HttpIssuerClient.class, ScanProbe.class)
                .doesNotContain(NotAComponent.class, CardIssuerClient.class);
        assertThat(InitLog.INITIALIZED).as("static initializers that ran").doesNotContain("ScanProbe");
    }
}
